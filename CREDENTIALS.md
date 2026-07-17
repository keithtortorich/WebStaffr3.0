# WebStaffr Credentials & Onboarding

## Required Environment Variables

### 1. `GROK_API_KEY` (for `GrokVoiceBackend`)
- **Purpose**: enables real chat via xAI's Grok API in Angel.
- **How to get**: your xAI account's API key management page. `[Unverified]`
  the exact current URL -- check xAI's own docs rather than trusting a
  hardcoded link here, since these change.
- **Behavior**:
  - Set -> `GrokVoiceBackend` is used (see `webstaffr/workers/angel/voice.py`).
  - Unset -> falls back to `NullVoiceBackend` (safe, deterministic, no
    external calls).
- **Status**: implemented against xAI's chat-completions endpoint. The
  model name and endpoint are `[Unverified]` against a live account --
  nobody with access to a real xAI account has exercised this yet.
- **Security**: never commit. Use a local, gitignored `.env` file or your
  shell environment.

### 2. `GHL_API_KEY` + `GHL_LOCATION_ID` (for `GoHighLevelClient`)
- **Purpose**: real appointment and note syncing to GoHighLevel.
- **How to get**: GoHighLevel's developer/API settings for your location.
- **Behavior**:
  - Both set -> real `GoHighLevelClient` is used.
  - Either missing -> `NullGHLClient` (records calls in memory, no network
    calls -- safe default for tests and unconfigured tenants).
- **Status**: `create_appointment`, `log_note`, `update_appointment`, and
  `cancel_appointment` are all implemented (see
  `webstaffr/workers/angel/ghl.py`). GHL sync calls in `Angel` retry up
  to 3 times (configurable via `Angel(..., ghl_max_attempts=N)`) before
  giving up and logging the failure -- a sync failure never blocks a
  booking or a conversation turn. Real endpoint paths/payload shapes for
  `update_appointment`/`cancel_appointment` are `[Unverified]` against a
  live GHL account.
- **Security**: never commit. Same as above.

### 3. `RETELL_WEBHOOK_SECRET` (for Retell AI voice/telephony webhooks)
- **Purpose**: verifies that `/retell/webhook` and `/retell/function-call`
  requests actually came from Retell before trusting the payload.
- **How to get**: issued by Retell when you register a webhook in their
  dashboard.
- **Behavior**:
  - Set -> `RetellSignatureVerifier` is used (HMAC-SHA256 over the raw
    request body).
  - Unset -> falls back to `NullRetellWebhookVerifier` (accepts everything
    -- safe default for tests and local dev, never intended for a real
    deployment).
- **Status**: `[Unverified]` -- implemented from Retell's publicly
  documented webhook-signing convention, not yet exercised against a real
  Retell-signed request. Confirm the exact signature header name/format in
  Retell's dashboard/docs before relying on this in production; same
  caveat GHL's endpoint paths carried before they were checked against
  live docs on 2026-07-08 (see `webstaffr/workers/angel/retell.py`).
- **Tenant resolution**: each tenant's Retell agent/phone number must be
  configured in the Retell dashboard with `metadata: {"tenant_id": "..."}`
  -- Retell echoes this back on every webhook/function-call payload for
  that call. There is no phone-number-to-tenant lookup table in this repo
  (a real schema change, not done); this is a first-slice design for a
  handful of pilot tenants configured by hand.
- **Not required to receive webhooks**: `RETELL_API_KEY` is not needed for
  `/retell/webhook` or `/retell/function-call` to work -- it would only be
  needed for this app to call Retell's own management API (e.g.
  programmatically creating/updating an agent), which nothing in this repo
  does yet.
- **Security**: never commit. Same as above.

### 4. `GHL_WEBHOOK_SECRET` (for `/webhooks/ghl` shared-secret auth)
- **Purpose**: verifies that `/webhooks/ghl` requests actually came from
  GoHighLevel before trusting the payload. Added 2026-07-08 after
  `CODE_REVIEW.md` flagged this endpoint (High) as accepting `tenant_id` --
  a public value, not a secret -- as its only scoping check.
- **How to get**: not issued by GHL -- you choose this value yourself and
  configure it as a custom header (`X-Webhook-Secret: <value>`) on
  GoHighLevel's workflow Webhook action. GHL does not sign outgoing
  webhooks itself, so a shared secret set on both sides is the mechanism.
- **Behavior**:
  - Set -> `StaticSecretVerifier` checks the `X-Webhook-Secret` header
    (constant-time comparison); missing or mismatched -> `401`.
  - Unset -> falls back to `NullSharedSecretVerifier` (accepts everything
    -- same unconfigured-fails-open shape as `RETELL_WEBHOOK_SECRET`, safe
    for tests and local dev, not intended for a real deployment).
- **Status**: implemented and tested (`tests/test_router.py`); not yet
  exercised against a real GHL workflow, since no live GHL account exists
  yet (see `TASKS.md`).
- **Security**: never commit. Same as above.

### 5. `BOOK_API_KEY` (for `/book` shared-secret auth)
- **Purpose**: verifies the caller of `/book` before letting it create an
  appointment for an arbitrary `tenant_id`. Added same session/reason as
  `GHL_WEBHOOK_SECRET` above.
- **How to get**: not issued by anything external -- you choose this value
  and give it to whatever calls `/book` directly (there is no live caller
  today; this is for a future booking UI or server-side integration).
- **Behavior**:
  - Set -> `StaticSecretVerifier` checks the `X-API-Key` header; missing or
    mismatched -> `401`.
  - Unset -> falls back to `NullSharedSecretVerifier` (accepts everything).
- **Status**: implemented and tested; no real caller configured yet.
- **Security**: never commit. Same as above.

### 6. `SERVICETITAN_CLIENT_ID` + `SERVICETITAN_CLIENT_SECRET` + `SERVICETITAN_TENANT_ID` (+ optional `SERVICETITAN_BASE_URL`)
- **Purpose**: read-first polling of jobs, customers, appointments, invoices,
  payments, locations, projects, installed equipment, and technicians.
- **Behavior**:
  - All three required vars set -> `webstaffr/integrations/servicetitan/client.py`
    builds a real `ServiceTitanClient`. Missing any one raises
    `ServiceTitanNotConfiguredError` at construction time; the
    `/integrations/servicetitan/poll` endpoint surfaces this as a `503`.
- **Status**: client and sync logic are implemented and have offline unit tests in
  `tests/test_servicetitan.py`. The polling endpoint is behind
  `SERVICETITAN_ENABLED=true` in `router.py`; no live ServiceTitan account has
  been exercised yet. Endpoint paths/payload shapes are `[Unverified]` against
  a live ServiceTitan tenant until exercised with real credentials.
- **Security**: never commit. Same as above.

## Local Development Setup

```bash
# 1. Create .env in the repo root (already gitignored -- see .gitignore)
cat > .env << 'EOF'
GROK_API_KEY=your_xai_key_here
GHL_API_KEY=your_ghl_key_here
GHL_LOCATION_ID=your_location_id_here
RETELL_WEBHOOK_SECRET=your_retell_webhook_signing_secret_here
GHL_WEBHOOK_SECRET=choose_your_own_shared_secret_here
BOOK_API_KEY=choose_your_own_api_key_here
WEBSTAFFR_DB_PATH=./webstaffr.db
EOF

# 2. Run with real backends
export $(cat .env | xargs)
uvicorn webstaffr.workers.angel.router:app --reload
```

## Testing

- The full test suite always runs, regardless of environment -- nothing
  is conditionally skipped based on whether credentials are set.
- Credential-check tests explicitly clear the relevant env var to verify
  the "not configured" error path (e.g. `test_grok_backend_requires_api_key`).
- Behavior tests pass an explicit fake key (e.g. `GrokVoiceBackend(api_key="test-key")`)
  to exercise the real logic without needing a live account, then mock
  the actual network call (`httpx`/`_request`) rather than hitting a
  real API. No test in this suite makes a real network call.
- Run the full suite: `python -m pytest tests/` (or `python -m unittest discover -s tests`)
- Run the self-healing health check: `python scripts/health_check.py`
- Once you've set real `GROK_API_KEY` / `GHL_API_KEY`+`GHL_LOCATION_ID`, verify each
  against the live vendor API with `scripts/test_grok_connection.py` and
  `scripts/test_ghl_connection.py` -- run these yourself in your own terminal
  (not through Claude), same reasoning as `scripts/test_db_connection.py`:
  the key is masked via `getpass` and never appears in any chat/session.
  Both are read-only/no-side-effect calls and throwaway diagnostics -- safe
  to delete once you've confirmed the real credentials work.

## Production Notes

- Use a real secret manager for deployment (Docker secrets, AWS Secrets
  Manager, etc.) rather than a `.env` file -- `.env` is a local
  development convenience only.
- Watch logs for `VoiceBackendNotConfiguredError` / `GHLNotConfiguredError`
  (raised at construction if credentials are missing) and for
  `ghl_call_attempt_failed` / `ghl_sync_failed` / `ghl_note_log_failed`
  (logged, not raised, when a configured GHL call still fails after
  retrying).
- No hosting/deployment decision has been made yet for this repo.
