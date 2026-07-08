"""Shared-secret authentication for the two server-to-server endpoints that
have no browser caller and are therefore not in ScopedCORSMiddleware's
CORS-scoped set: /book and /webhooks/ghl. CODE_REVIEW.md (2026-07-08)
flagged both as High-severity: they accept `tenant_id` -- a public value,
returned in API responses and embedded in generated-site page source -- as
if it were a credential, with no auth of any kind.

Same Null-object + env-driven pattern as retell.py's RetellWebhookVerifier:
an unset secret falls back to a Null verifier that accepts everything
(consistent with NullVoiceBackend/NullGHLClient/NullRetellWebhookVerifier),
so tests and a not-yet-configured deployment never require credentials to
run. Once the relevant env var is set, a missing or mismatched header is
rejected with 401.

[Inference]: this closes the gap only once the founder actually sets
GHL_WEBHOOK_SECRET / BOOK_API_KEY as real deployment secrets -- an
unconfigured instance is unchanged from today (open). That's a deliberate
continuation of this repo's existing convention (Retell's own webhook
verification has the identical unconfigured-fail-open shape), not a
compromise unique to this fix. Flagged explicitly rather than silently
matched, since "auth that doesn't protect until configured" is a real
tradeoff worth the founder knowing about, not assuming away.

This is a minimal shared-secret header, not a full auth system -- no
sessions, no per-caller identity, no token expiry/rotation. That matches
CODE_REVIEW.md's own recommendation ("even a minimal shared-secret/API-key
header") rather than building a larger auth system, which is out of MVP
scope per CLAUDE.md.
"""

from __future__ import annotations

import hmac
import os
from typing import Optional, Protocol


class SharedSecretVerifier(Protocol):
    def verify(self, provided: Optional[str]) -> bool: ...


class NullSharedSecretVerifier:
    """Accepts everything -- safe default for tests and before the relevant
    secret env var is set. Same pattern as NullVoiceBackend/NullGHLClient/
    NullRetellWebhookVerifier: an explicit, named no-op, not a silent skip."""

    def verify(self, provided: Optional[str]) -> bool:
        return True


class StaticSecretVerifier:
    """Constant-time comparison against a configured secret. Fails closed:
    a missing or mismatched header returns False rather than raising, so a
    caller can always treat "not verify()" as "reject the request" without
    a second exception-handling path -- same contract as
    RetellSignatureVerifier.verify()."""

    def __init__(self, secret: str) -> None:
        if not secret:
            raise ValueError("StaticSecretVerifier requires a non-empty secret.")
        self._secret = secret

    def verify(self, provided: Optional[str]) -> bool:
        if not provided:
            return False
        return hmac.compare_digest(self._secret, provided)


def ghl_webhook_verifier_from_env() -> SharedSecretVerifier:
    """GHL_WEBHOOK_SECRET set -> real verification against the
    X-Webhook-Secret header. Unset -> Null, matching
    _backend_from_env()/_ghl_client_from_env()/verifier_from_env() in
    router.py/retell.py: never silently construct something that will fail
    on first real use, and never require credentials to run tests or local
    dev. Configure this as a custom header on GoHighLevel's workflow
    Webhook action -- GHL does not sign outgoing webhooks itself, so a
    shared secret set on both sides is the mechanism, not HMAC over the
    body."""
    secret = os.environ.get("GHL_WEBHOOK_SECRET")
    if secret:
        return StaticSecretVerifier(secret)
    return NullSharedSecretVerifier()


def book_api_verifier_from_env() -> SharedSecretVerifier:
    """BOOK_API_KEY set -> real verification against the X-API-Key header.
    Unset -> Null. /book has no browser caller today (see router.py's
    docstring) -- this is for a future booking UI or server-side
    integration, whichever calls it first."""
    secret = os.environ.get("BOOK_API_KEY")
    if secret:
        return StaticSecretVerifier(secret)
    return NullSharedSecretVerifier()
