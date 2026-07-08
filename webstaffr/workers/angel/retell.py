"""Retell AI integration for Angel's voice/telephony layer.

Retell hosts the live phone call and the persistent realtime audio session
itself -- this app never holds a WebSocket open for the duration of a call.
That split was a deliberate decision, not a default: native Grok Voice Agent
API would have required this app to hold that connection itself, which is
incompatible with the current Vercel serverless deployment (see the
"voice vendor hosting constraint" memory note, 2026-07-08). Retell (and
Vapi) absorb that job into their own infrastructure; this app only ever
needs to answer short HTTP requests -- which is what retell_router.py does.

This module holds the one piece of real logic Retell integration needs
beyond thin webhook handling: verifying that a webhook actually came from
Retell before trusting its payload.

[Unverified]: implemented from Retell's publicly documented webhook-signing
convention (HMAC-SHA256 over the raw request body, secret issued when a
webhook is registered). Not yet exercised against a real Retell-signed
request -- same status GoHighLevelClient's endpoint paths carried before
they were checked against live docs on 2026-07-08. Confirm the exact header
name and signature format in Retell's dashboard/docs before relying on this
in production; the header name and prefix-stripping logic below are best
guesses at a stable convention, not a confirmed contract.
"""

from __future__ import annotations

import hashlib
import hmac
import os
from typing import Optional, Protocol


class RetellWebhookVerifier(Protocol):
    def verify(self, payload: bytes, signature_header: Optional[str]) -> bool: ...


class NullRetellWebhookVerifier:
    """Accepts everything -- safe default for tests and for local dev before
    RETELL_WEBHOOK_SECRET is set. Same pattern as NullVoiceBackend and
    NullGHLClient: an explicit, named no-op rather than a silent skip."""

    def verify(self, payload: bytes, signature_header: Optional[str]) -> bool:
        return True


class RetellSignatureVerifier:
    """HMAC-SHA256 verification against a signing secret. [Unverified] --
    see module docstring. Fails closed: any missing header, malformed
    header, or mismatch returns False rather than raising, so a caller can
    always treat "not verify()" as "reject the request" without a second
    exception-handling path."""

    def __init__(self, signing_secret: str) -> None:
        if not signing_secret:
            raise ValueError("RetellSignatureVerifier requires a non-empty signing secret.")
        self._secret = signing_secret.encode("utf-8")

    def verify(self, payload: bytes, signature_header: Optional[str]) -> bool:
        if not signature_header:
            return False
        expected = hmac.new(self._secret, payload, hashlib.sha256).hexdigest()
        # Some webhook providers prefix the digest with a scheme, e.g.
        # "v1,<hex>" or "sha256=<hex>" -- take whatever follows the last
        # separator so either a bare hex digest or a prefixed one verifies
        # the same way. Confirm Retell's actual format before depending on
        # this in production.
        candidate = signature_header.replace("=", ",").split(",")[-1].strip()
        return hmac.compare_digest(expected, candidate)


def verifier_from_env() -> RetellWebhookVerifier:
    """RETELL_WEBHOOK_SECRET set -> real verification. Unset -> Null,
    matching _backend_from_env()/_ghl_client_from_env() in router.py: never
    silently construct something that will fail on first real use, and
    never require credentials to run tests or local dev."""
    secret = os.environ.get("RETELL_WEBHOOK_SECRET")
    if secret:
        return RetellSignatureVerifier(secret)
    return NullRetellWebhookVerifier()
