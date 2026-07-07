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

## Blocked (on founder's own decision, not external)

- **GHL signup + `GHL_API_KEY`/`GHL_LOCATION_ID`.** Founder deliberately hasn't signed up yet — it's a 30-day trial and he wants to control when that clock starts. GoHighLevel signup page is open in a browser tab, waiting. Do not proceed until he says he's ready.

## Not yet started

- **`GROK_API_KEY`: done.** Real key generated at `console.x.ai` (2026-07-08), set as a Sensitive Vercel env var (Production + Preview), production redeployed to pick it up. Founder still needs to add xAI API credits himself (skipped that purchase step — Claude doesn't complete purchases) before real calls will succeed. End-to-end verification via `/chat` is still blocked on the Supabase incident below (DB unreachable → 503 before the request ever reaches Grok).
- Once Supabase clears: confirm `/sites/{tenant_id}` returns real data end-to-end (Vercel backend → Lovable frontend → Angel widget) with an actual intake submission, and verify `GROK_API_KEY` works via a real `/chat` call.
- Once founder starts the GHL trial: create the Private Integration Token + note `GHL_LOCATION_ID`, wire both into Vercel the same way as `GROK_API_KEY`.
- Delete the throwaway diagnostic scripts in `scripts/` once the Supabase connection and both credentials are confirmed stable.
- No auth, CI/CD, or production-readiness decision made yet beyond what's documented in `CLAUDE.md`.

## Reference

- Live backend: `https://web-staffr3-0-snowy.vercel.app` (`/health` confirmed working; DB-touching routes 503 until Supabase clears)
- Lovable "Site Weaver": project ID `27e51275-323a-4156-a7f9-9bc41c7bf36c`
- Latest commit pushed: `efc2ad3` on `origin/main`
- Full session history and rationale: `CLAUDE.md` (session addenda, chronological, most recent at bottom)
- Findings from the original (pre-`WebStaffr-clean`) repo and Google Drive, re-examined 2026-07-08 for anything useful not carried forward (brand/positioning docs, locked pricing tiers, beachhead niche, unmigrated agent code, CAC/churn/fundraising inconsistencies across Drive, AOKAI lead): `LEGACY_AUDIT.md`. Assessment only — nothing in it has been applied to this repo.
- Business-strategy cross-check (pricing, niche/expansion sequence, CAC/churn reconciliation, and the voice-vs-chat positioning gap — the product is chat-only today, no phone voice built): `STRATEGY.md`. Reference only — no code or pricing changes made from it.
