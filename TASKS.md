# TASKS.md — WebStaffr 3.0

Working task list for the intake → generated customer site → Angel widget MVP flow (see `CLAUDE.md` for full operational history/decisions, `PROJECT.md` for product vision). Kept here so state survives across chat sessions.

Last updated: 2026-07-08.

## Blocked (external, not actionable right now)

- **#12 — Deploy backend to Vercel/Netlify with Supabase connection.** Code is deploy-ready and live on Vercel (`https://web-staffr3-0-snowy.vercel.app`), but `DATABASE_URL` still won't authenticate against Supabase. Root cause isolated to an active, unresolved Supabase platform incident (degraded compute capacity in `ap-south-1`, this project's region) — not a code or config defect. Founder decision: wait it out, retry later.
  - **Next step when retrying:** run `scripts/test_db_connection.py` with the existing (already Sensitive-stored) Vercel `DATABASE_URL` value first. If Supabase's incident has cleared, this should just work — no redeploy needed on either the backend or the Lovable frontend. If it still fails, reset the Supabase password again, rebuild the connection string with `scripts/build_database_url.py`, re-set `DATABASE_URL` via `vercel env add DATABASE_URL production` (CLI already installed + authenticated on the founder's Mac), then `vercel --prod --yes` from the linked project directory.
  - Check `status.supabase.com` first to confirm the incident has actually cleared before spending another retry cycle.
  - Diagnostic scripts `scripts/test_db_connection.py` and `scripts/build_database_url.py` are throwaway — safe to delete once this is resolved.

## Completed

- #1–#7 — Backend intake flow: `intake_submissions` migration, `POST /intake`, tests, `GET /sites/{tenant_id}`, Lovable "Site Weaver" multi-tenant site project created.
- #8 — Hosting decision made and executed: Supabase Postgres + Vercel (reconciled from `[pending]` — the decision was made and largely built out earlier, just hadn't been marked done).
- #9 — Vercel FastAPI/ASGI support confirmed working (via root `index.py` entrypoint, not `pyproject.toml` — that approach broke the build).
- #10 — Supabase Postgres project set up, migrations `0001`–`0004` applied (including RLS default-deny).
- #11, #14–#19 — Dual-backend (SQLite/Postgres) persistence layer built, RLS applied, `psycopg2-binary` added, full 81-test suite passing against SQLite.
- #13 — Lovable site pointed at the real deployed backend URL. Lovable's agent worked around a reserved `VITE_` secret-prefix restriction by using `API_BASE_URL` (with `VITE_API_BASE_URL` kept as a fallback) and updating `vite.config.ts`'s `envPrefix`. Verified live preview still renders.
- #20 — Fixed a real, unrelated bug: `requirements-dev.txt` pinned `pytest==9.1.1`, which doesn't exist on PyPI, silently breaking the README's documented fresh-install steps. Repinned to real `8.4.2`. Also discovered no `.venv` actually existed locally despite prior "81/81 passing" claims — built one for real and reverified.
- #21 — Fixed a real production bug found via `get_runtime_errors`: the ASGI lifespan handler was opening a DB connection at cold start just to call `migrate()` (a documented no-op under Postgres), meaning the Supabase outage was crashing the *entire* app — including `/health` — not just DB-touching routes. Fixed to skip that connection under Postgres. Also fixed 5 route handlers that let raw DB exceptions (including the Supavisor pooler hostname) leak to clients instead of returning a clean 503. **Verified live**: `/health` now returns `200` on the real Vercel deployment right now, while the Supabase incident is still open.

## In Progress

- **#22 — Retell AI voice/telephony integration (first draft, 2026-07-08).** Voice-vendor decision: Retell, not native Grok Voice Agent API (ruled out — would require this app to hold a persistent per-call WebSocket for the call's duration, incompatible with the current Vercel serverless deployment) and not Vapi (needs a separate telephony vendor on top, more integration/tuning effort than a solo-founder team has spare right now). Rationale detail: see chat history and `memory/project_webstaffr_voice_vendor_hosting_constraint.md`.
  - Built: `webstaffr/workers/angel/retell.py` (webhook signature verification — `RetellSignatureVerifier` + `NullRetellWebhookVerifier`), `webstaffr/workers/angel/retell_router.py` (`POST /retell/webhook` for call lifecycle, `POST /retell/function-call` for `book_appointment`/`escalate_to_human`/`get_availability`), mounted into `create_app()` in `router.py`. Reuses `Angel`/`AppointmentRepository`/`get_connection()` directly — no SQLAlchemy, no new persistence pattern, no schema/migration change.
  - `CREDENTIALS.md` updated: `RETELL_WEBHOOK_SECRET` documented. `RETELL_API_KEY` is *not* required just to receive webhooks.
  - Tests: 21 new (`tests/test_retell_router.py`) — full suite now 102/102 passing, health check HEALTHY.
  - **Not yet done / blocked on founder action:** no real Retell account, agent, or phone number exists yet. Tenant-to-phone-number resolution is via per-tenant `metadata: {"tenant_id": "..."}` configured by hand in Retell's dashboard (no DB table for this — deliberate, first-slice scope for a handful of pilot tenants). Signature header name/format and function-call payload shape are `[Unverified]` — implemented from Retell's public docs, not yet exercised against a live account. Voice-booked appointments currently save locally but do **not** sync to GHL (`sync_to_ghl=False` in the function-call handler) — a fresh phone caller has no existing GHL contact_id, and contact lookup/creation isn't built yet.
  - Nothing pushed/deployed as of the code being written; see Reference section below for push status.

## Blocked (on founder's own decision, not external)

- **GHL signup + `GHL_API_KEY`/`GHL_LOCATION_ID`.** Founder deliberately hasn't signed up yet — it's a 30-day trial and he wants to control when that clock starts. GoHighLevel signup page is open in a browser tab, waiting. Do not proceed until he says he's ready.

## Not yet started

- **`GROK_API_KEY`: done.** Real key generated at `console.x.ai` (2026-07-08), set as a Sensitive Vercel env var (Production + Preview), production redeployed to pick it up. Founder still needs to add xAI API credits himself (skipped that purchase step — Claude doesn't complete purchases) before real calls will succeed. End-to-end verification via `/chat` is still blocked on the Supabase incident below (DB unreachable → 503 before the request ever reaches Grok).
- Once Supabase clears: confirm `/sites/{tenant_id}` returns real data end-to-end (Vercel backend → Lovable frontend → Angel widget) with an actual intake submission, and verify `GROK_API_KEY` works via a real `/chat` call.
- Once founder starts the GHL trial: create the Private Integration Token + note `GHL_LOCATION_ID`, wire both into Vercel the same way as `GROK_API_KEY`.
- Retell: register a real phone number/agent in Retell's dashboard, set `RETELL_WEBHOOK_SECRET` (local `.env` and/or Vercel), point the agent's webhook URLs at `/retell/webhook` and `/retell/function-call` on the deployed backend, then verify the signature format and payload shapes against a real test call before trusting this for a paying pilot account.
- Delete the throwaway diagnostic scripts in `scripts/` once the Supabase connection and both credentials are confirmed stable.
- No auth, CI/CD, or production-readiness decision made yet beyond what's documented in `CLAUDE.md`.

## Reference

- Live backend: `https://web-staffr3-0-snowy.vercel.app` (`/health` confirmed working; DB-touching routes 503 until Supabase clears)
- Lovable "Site Weaver": project ID `27e51275-323a-4156-a7f9-9bc41c7bf36c`
- Latest commit pushed: `efc2ad3` on `origin/main`
- Full session history and rationale: `CLAUDE.md` (session addenda, chronological, most recent at bottom)
- Findings from the original (pre-`WebStaffr-clean`) repo and Google Drive, re-examined 2026-07-08 for anything useful not carried forward (brand/positioning docs, locked pricing tiers, beachhead niche, unmigrated agent code, CAC/churn/fundraising inconsistencies across Drive, AOKAI lead): `LEGACY_AUDIT.md`. Assessment only — nothing in it has been applied to this repo.
- Business-strategy cross-check (pricing, niche/expansion sequence, CAC/churn reconciliation, and the voice-vs-chat positioning gap — the product is chat-only today, no phone voice built): `STRATEGY.md`. Reference only — no code or pricing changes made from it.
