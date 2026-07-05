"""FastAPI webhook handler for GoHighLevel events. Starts an Angel session
for the relevant tenant when GHL sends a website-lead or missed-call event.

Kept intentionally thin: the router's job is to validate the incoming
payload, resolve a Tenant, and hand off to Angel -- not to contain Angel's
own logic.
"""

from __future__ import annotations

import logging
import sqlite3
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel

from ...db import connect, migrate
from ...intake_router import intake_router
from ...tenant import InvalidTenantError, Tenant
from .angel import Angel
from .ghl import GHLClient
from .voice import VoiceBackend

logger = logging.getLogger("webstaffr.angel.router")


class GHLWebhookEvent(BaseModel):
    """Minimal shape of the GHL events this router handles. GHL's real
    payloads carry more fields than this -- extra fields are ignored by
    pydantic by default, so this stays intentionally narrow to what Angel
    actually needs, carrying forward the "treat external input as
    untrusted, validate before use" principle from the core executor."""

    tenant_id: str
    event_type: str  # e.g. "website_lead", "missed_call"
    contact_id: Optional[str] = None
    contact_name: Optional[str] = None
    message: Optional[str] = None


class ChatRequest(BaseModel):
    tenant_id: str
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str


class BookAppointmentRequest(BaseModel):
    """Exposes Angel.book_appointment over HTTP. Previously only reachable
    in-process (e.g. from the /chat or /webhooks/ghl handlers) -- this is
    for callers that want to book directly without going through a
    conversation turn at all (a future booking UI, a server-side
    integration, etc.)."""

    tenant_id: str
    contact_name: str
    starts_at: str
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    notes: Optional[str] = None
    sync_to_ghl: bool = True
    ghl_contact_id: Optional[str] = None


class BookAppointmentResponse(BaseModel):
    appointment_id: int
    tenant_id: str
    contact_name: str
    starts_at: str
    ghl_synced: bool


SUPPORTED_EVENT_TYPES = {"website_lead", "missed_call"}

# Paths called directly from browser JS running on an arbitrary origin --
# the customer-site widget (angel-widget.js) for /chat, and the intake
# form (wherever it's hosted -- the WebStaffr marketing site today, a
# Lovable-generated page later) for /intake and its read-only presets
# endpoints. These are the only paths that need CORS headers. /book and
# /webhooks/ghl are not meant to be readable by browser JS running on an
# arbitrary third-party origin -- /webhooks/ghl is only ever called
# server-to-server by GoHighLevel (CORS is a browser-enforced restriction
# and has no bearing on that caller), and /book has no browser caller
# today. Scoping here means adding a browser-facing caller for /book later
# requires a deliberate change to this set, not an accidental side effect
# of the app-wide wildcard that used to be here.
_CORS_SCOPED_PATHS = {"/chat", "/intake"}
# Prefixes rather than exact paths, for routes with a path parameter
# (/intake/presets/{industry}) -- exact-match membership in
# _CORS_SCOPED_PATHS can't match a dynamic segment.
_CORS_SCOPED_PREFIXES = ("/intake/presets",)


class ScopedCORSMiddleware(BaseHTTPMiddleware):
    """CORS restricted to `_CORS_SCOPED_PATHS`/`_CORS_SCOPED_PREFIXES`,
    replacing FastAPI's CORSMiddleware which is app-wide only. See the
    CLAUDE.md session addendum (2026-07-05) for why this replaced a
    wildcard `allow_origins` that covered /book and /webhooks/ghl as an
    unintended side effect."""

    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")
        path = request.url.path
        scoped = path in _CORS_SCOPED_PATHS or path.startswith(_CORS_SCOPED_PREFIXES)

        if scoped and request.method == "OPTIONS":
            response = Response(status_code=200)
        else:
            response = await call_next(request)

        if scoped and origin:
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "*"

        return response


def create_app(
    db_path: str = "webstaffr.db",
    voice_backend: Optional[VoiceBackend] = None,
    ghl_client: Optional[GHLClient] = None,
) -> FastAPI:
    """Factory rather than a module-level app instance, so tests (and
    Docker, and any future multi-tenant deployment shape) can construct an
    app pointed at a specific database and specific backends instead of
    relying on hidden global state.

    IMPORTANT: this module also builds a default `app` instance at import
    time (see bottom of file), for `uvicorn ...:app`. Migration must NOT
    run eagerly inside this factory itself -- that would make merely
    importing this module (as every test and the health check does) touch
    disk and create/migrate a real db file as a side effect, independent
    of whether that app instance is ever actually served. Migration stays
    scoped to the ASGI lifespan event below, which only fires when the app
    is actually started."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        with connect(db_path) as conn:
            migrate(conn)
        yield

    app = FastAPI(title="WebStaffr Angel Router", lifespan=lifespan)
    app.state.db_path = db_path  # read by intake_router's _get_connection()
    app.include_router(intake_router)

    # The widget is embedded on customer websites (arbitrary origins), so
    # /chat needs CORS enabled; the intake form (wherever it's hosted) needs
    # the same for /intake. Scoped to just those paths -- see
    # ScopedCORSMiddleware above -- rather than the app-wide wildcard this
    # used to be (which also covered /book and /webhooks/ghl as an
    # unintended side effect; see CLAUDE.md session addendum 2026-07-05).
    app.add_middleware(ScopedCORSMiddleware)

    def get_connection() -> sqlite3.Connection:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.post("/chat", response_model=ChatResponse)
    def chat(req: ChatRequest) -> ChatResponse:
        """Used by angel-widget.js on generated customer sites -- a direct
        chat turn, separate from the GHL webhook flow above."""
        try:
            tenant = Tenant(tenant_id=req.tenant_id)
        except InvalidTenantError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        conn = get_connection()
        try:
            angel = Angel(tenant=tenant, conn=conn, voice_backend=voice_backend, ghl_client=ghl_client)
            reply = angel.respond(req.message)
            conn.commit()
        finally:
            conn.close()

        logger.info("chat_handled tenant=%s", req.tenant_id)
        return ChatResponse(reply=reply)

    @app.post("/book", response_model=BookAppointmentResponse)
    def book(req: BookAppointmentRequest) -> BookAppointmentResponse:
        """Direct booking endpoint -- same underlying Angel.book_appointment
        used by /chat and /webhooks/ghl, exposed for callers that don't go
        through a conversation turn. Untrusted input is validated the same
        way as the other endpoints: reject before touching the DB, not
        after."""
        try:
            tenant = Tenant(tenant_id=req.tenant_id)
        except InvalidTenantError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        if not req.contact_name.strip():
            raise HTTPException(status_code=400, detail="contact_name must not be empty")
        if not req.starts_at.strip():
            raise HTTPException(status_code=400, detail="starts_at must not be empty")

        conn = get_connection()
        try:
            angel = Angel(tenant=tenant, conn=conn, voice_backend=voice_backend, ghl_client=ghl_client)
            appt = angel.book_appointment(
                contact_name=req.contact_name,
                starts_at=req.starts_at,
                contact_phone=req.contact_phone,
                contact_email=req.contact_email,
                notes=req.notes,
                sync_to_ghl=req.sync_to_ghl,
                ghl_contact_id=req.ghl_contact_id,
            )
            conn.commit()
        finally:
            conn.close()

        logger.info(
            "appointment_booked_via_http tenant=%s appointment_id=%s",
            req.tenant_id,
            appt.appointment_id,
        )
        return BookAppointmentResponse(
            appointment_id=appt.appointment_id,
            tenant_id=appt.tenant_id,
            contact_name=appt.contact_name,
            starts_at=appt.starts_at,
            ghl_synced=appt.ghl_synced,
        )

    @app.post("/webhooks/ghl")
    def ghl_webhook(event: GHLWebhookEvent) -> dict:
        try:
            tenant = Tenant(tenant_id=event.tenant_id)
        except InvalidTenantError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        if event.event_type not in SUPPORTED_EVENT_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported event_type: {event.event_type!r}. "
                f"Supported: {sorted(SUPPORTED_EVENT_TYPES)}",
            )

        conn = get_connection()
        try:
            angel = Angel(
                tenant=tenant,
                conn=conn,
                voice_backend=voice_backend,
                ghl_client=ghl_client,
            )
            reply = angel.respond(
                event.message or f"New {event.event_type} from {event.contact_name or 'a contact'}.",
                extra_context={"event_type": event.event_type, "contact_id": event.contact_id},
            )
            conn.commit()
        finally:
            conn.close()

        logger.info(
            "ghl_webhook_handled tenant=%s event_type=%s",
            event.tenant_id,
            event.event_type,
        )
        return {"status": "handled", "reply": reply}

    return app


def _backend_from_env() -> Optional[VoiceBackend]:
    """GrokVoiceBackend only if GROK_API_KEY is actually set -- otherwise
    None, so create_app() falls back to NullVoiceBackend. Never silently
    construct a backend that will fail on first real use."""
    import os

    if os.environ.get("GROK_API_KEY"):
        from .voice import GrokVoiceBackend

        return GrokVoiceBackend()
    return None


def _ghl_client_from_env() -> Optional[GHLClient]:
    import os

    if os.environ.get("GHL_API_KEY") and os.environ.get("GHL_LOCATION_ID"):
        from .ghl import GoHighLevelClient

        return GoHighLevelClient()
    return None


# Default app instance for `uvicorn webstaffr.workers.angel.router:app`.
# db_path and backends are picked up from environment at process start --
# see Dockerfile (WEBSTAFFR_DB_PATH) and docker-compose.yml (credentials).
import os as _os  # noqa: E402

app = create_app(
    db_path=_os.environ.get("WEBSTAFFR_DB_PATH", "webstaffr.db"),
    voice_backend=_backend_from_env(),
    ghl_client=_ghl_client_from_env(),
)
