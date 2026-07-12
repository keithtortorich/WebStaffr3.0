"""FastAPI router for Retell AI webhooks: call lifecycle events and
mid-call function/tool calls.

Kept thin per the same philosophy as ghl.py's webhook router (see
router.py's GHLWebhookEvent docstring): validate the incoming payload,
resolve a Tenant, hand off to Angel/AppointmentRepository -- this module
does not contain Angel's own logic. Retell hosts the live call and its
persistent realtime session; this app only ever answers short HTTP
requests here. See retell.py's module docstring for why, and for the
[Unverified] status of signature verification.

Tenant resolution: each tenant's Retell agent/phone number is configured
in the Retell dashboard with `metadata: {"tenant_id": "..."}`, which Retell
echoes back on every webhook/function-call payload for that call. This
avoids a new phone-number-to-tenant lookup table (a real schema/migration
change) for a first slice covering a handful of pilot tenants -- revisit
if/when phone numbers need to be provisioned programmatically at scale.

Payload shapes below (event names, `call.metadata`, function-call
`name`/`args` fields) are implemented per Retell's publicly documented
webhook and custom-function conventions. [Unverified] against a live
Retell account -- confirm exact field names in Retell's dashboard/docs
before wiring a real agent to this.
"""

from __future__ import annotations

import json
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ...db import DB_ERRORS, get_connection
from ...tenant import InvalidTenantError, Tenant
from .angel import Angel
from .ghl import GHLClient
from .retell import RetellWebhookVerifier, verifier_from_env
from .voice import VoiceBackend

logger = logging.getLogger("webstaffr.angel.retell_router")

_SIGNATURE_HEADER = "x-retell-signature"

_FALLBACK_RESULT = (
    "I'm sorry, I'm having trouble with this call right now -- "
    "a team member will follow up with you shortly."
)


def _tenant_id_from_payload(payload: dict) -> Optional[str]:
    """Retell's call-lifecycle and function-call payloads nest metadata
    differently in different event shapes -- check both the top level and
    under `call` so either shape resolves the same way."""
    metadata = payload.get("metadata") or payload.get("call", {}).get("metadata") or {}
    return metadata.get("tenant_id")


class FunctionCallResult(BaseModel):
    """Retell expects a spoken-result string back from a function-call
    webhook so the voice agent can continue the conversation with it."""

    result: str


def create_retell_router(
    db_path: str,
    voice_backend: Optional[VoiceBackend],
    ghl_client: Optional[GHLClient],
    verifier: Optional[RetellWebhookVerifier] = None,
) -> APIRouter:
    """Factory, mirroring create_app() in router.py, so tests can inject a
    verifier/backends without touching environment variables or real
    credentials."""

    router = APIRouter(prefix="/retell", tags=["retell"])
    active_verifier = verifier or verifier_from_env()

    def _get_connection():
        try:
            return get_connection(db_path)
        except DB_ERRORS as exc:
            raise HTTPException(status_code=503, detail="Service temporarily unavailable") from exc

    async def _verified_payload(request: Request) -> dict:
        """Reads the raw body (required for signature verification --
        request.json() would hide the exact bytes Retell signed), verifies
        it, and only then parses it as JSON. Malformed JSON after a valid
        signature is a 400, not a 401 -- those are different failure
        modes and should not look the same to the caller."""
        body = await request.body()
        signature = request.headers.get(_SIGNATURE_HEADER)
        if not active_verifier.verify(body, signature):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
        if not body:
            return {}
        try:
            return json.loads(body)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail="Malformed JSON payload") from exc

    @router.post("/webhook")
    async def call_lifecycle_webhook(request: Request) -> dict:
        """Call lifecycle events (call_started, call_ended, etc.). Missing
        or invalid tenant_id is logged and acknowledged rather than
        rejected with an error status -- Retell doesn't need to see this
        app's internal tenant-routing problems as a call-level failure."""
        payload = await _verified_payload(request)
        event_type = payload.get("event")
        call = payload.get("call", {}) or {}
        call_id = call.get("call_id")
        tenant_id = _tenant_id_from_payload(payload)

        if not tenant_id:
            logger.warning("retell_webhook_missing_tenant_id event=%s call_id=%s", event_type, call_id)
            return {"status": "ignored", "reason": "no tenant_id in call metadata"}

        try:
            tenant = Tenant(tenant_id=tenant_id)
        except InvalidTenantError:
            logger.warning("retell_webhook_invalid_tenant_id tenant_id=%r call_id=%s", tenant_id, call_id)
            return {"status": "ignored", "reason": "invalid tenant_id"}

        logger.info("retell_call_event tenant=%s event=%s call_id=%s", tenant.tenant_id, event_type, call_id)

        if event_type == "call_ended":
            call_analysis = call.get("call_analysis", {}) or {}
            summary = call_analysis.get("call_summary")
            ghl_contact_id = (call.get("metadata") or {}).get("ghl_contact_id")
            if summary and ghl_contact_id:
                conn = _get_connection()
                try:
                    angel = Angel(tenant=tenant, conn=conn, voice_backend=voice_backend, ghl_client=ghl_client)
                    angel.log_note_to_ghl(ghl_contact_id, f"Angel voice call summary: {summary}")
                    conn.commit()
                finally:
                    conn.close()

        return {"status": "received"}

    @router.post("/function-call", response_model=FunctionCallResult)
    async def function_call_webhook(request: Request) -> FunctionCallResult:
        """Invoked mid-call when the voice agent decides to call a tool.
        Always returns 200 with a spoken result, even on failure -- a raw
        error status here would leave the caller mid-conversation with
        nothing to say. Errors are logged and degrade to a fallback line
        instead."""
        payload = await _verified_payload(request)
        name = payload.get("name")
        args = payload.get("args") or {}
        tenant_id = _tenant_id_from_payload(payload)

        if not tenant_id:
            return FunctionCallResult(result=_FALLBACK_RESULT)

        try:
            tenant = Tenant(tenant_id=tenant_id)
        except InvalidTenantError:
            return FunctionCallResult(result=_FALLBACK_RESULT)

        conn = _get_connection()
        try:
            angel = Angel(tenant=tenant, conn=conn, voice_backend=voice_backend, ghl_client=ghl_client)

            if name == "book_appointment":
                result = _handle_book_appointment(angel, args, conn)
            elif name == "escalate_to_human":
                logger.info("retell_escalation tenant=%s reason=%s", tenant.tenant_id, args.get("reason"))
                result = "Let me connect you with a team member now."
            elif name == "get_availability":
                # MVP stub -- same fixed-slots scope get_availability had
                # in the original booking sketch. Replace with a real
                # calendar query later; not a Retell-specific gap.
                result = "We have openings today at 9am, 11am, 1pm, 3pm, and 5pm. Which works best?"
            else:
                logger.warning("retell_unknown_function name=%r tenant=%s", name, tenant.tenant_id)
                result = _FALLBACK_RESULT
        finally:
            conn.close()

        return FunctionCallResult(result=result)

    def _handle_book_appointment(angel: Angel, args: dict, conn) -> str:
        preferred_time = args.get("preferred_time")
        if not preferred_time or not preferred_time.strip():
            return "I didn't catch a valid time for that -- could you repeat the preferred time?"
        preferred_time = preferred_time.strip()
        try:
            # sync_to_ghl=False here: a fresh caller has no existing GHL
            # contact_id yet (Retell doesn't know one), and creating/
            # looking up a GHL contact from a phone number is separate,
            # not-yet-built work. The appointment is still recorded locally
            # first -- that's the source of truth per Angel.book_appointment's
            # own documented design. GHL sync for voice bookings is a
            # known follow-up, not silently dropped.
            appt = angel.book_appointment(
                contact_name=args.get("customer_name") or "Caller",
                starts_at=preferred_time,
                contact_phone=args.get("phone"),
                notes=args.get("notes"),
                sync_to_ghl=False,
            )
            conn.commit()
            return f"You're all set for {appt.starts_at}. You'll get a confirmation shortly."
        except DB_ERRORS:
            logger.exception("retell_booking_failed tenant=%s", angel.tenant.tenant_id)
            return "I'm having trouble booking that right now -- a team member will call you back."

    return router
