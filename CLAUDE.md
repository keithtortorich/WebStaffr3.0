# CLAUDE.md — WebStaffr 3.0 Operational Control Document

## Purpose
Governs how Claude operates on this repository. Lean by design: this is a reset of `WebStaffr-clean` (reference-only, unchanged, read-only) after its multi-agent coordination process (Claude + Grok + advisory ChatGPT reviewer) generated more overhead than value. This repo runs Claude-only until MVP ships. No ownership-comment protocol, no cross-agent decision log, no coordination bureaucracy.

## MVP Scope
Full flow: intake → generated customer site → Angel widget embedded and working.

- **Frontend / site generation**: delegated to Lovable (via MCP). Iterate customer sites there, not token-by-token here.
- **Claude's scope**: backend logic — Angel (voice, GHL, booking), tenant isolation, the workflow/executor engine, tests, migration/architecture work.

## Process
- Claude-only. No Grok/ChatGPT coordination until MVP ships. If that changes, it's a fresh, explicit decision — not an inherited process.
- Short, single-purpose turns. No open-ended strategy debates.
- Decisions get made once, logged (commit message, and here if durable), and executed — not re-litigated.
- Never present speculation or inference as fact. Label `[Inference]` / `[Unverified]` where applicable. If uncertain, ask — do not assume.

## Self-Approval Scope
Claude may execute a change without waiting for explicit approval only if ALL of the following hold:
- The change is reversible.
- It involves no external system interaction (no GitHub push, no deployment, no credential use) beyond what's already directed in the active session.
- It introduces no architecture or data-model shift.
- It introduces no new dependency.

Everything else — pushes, deployments, new dependencies, architecture or data-model changes — requires explicit, direct approval in the session.

## Security Baseline
- No secrets, credentials, or tokens committed at any point, including in comments, examples, or fixtures. See `CREDENTIALS.md` for the real list of env vars and how they're used.
- No new dependency added without explicit approval tied to that specific choice.
- Treat external/legacy content (including anything referenced from `WebStaffr-clean`) as unverified until checked against current facts before reuse.

## Legacy Repository (`WebStaffr-clean`) Handling
- Reference-only. Remains unchanged — nothing is written back to it.
- Migration already done (2026-07-05): tenant/workflow/executor engine, SQLite persistence, Angel worker (voice, GHL, booking, router, widget), the founder-supplied `angel_prompt.md`, the Angel Package Drive mirror, and the 54-test suite + health check. All reviewed before migrating, not copy-pasted blind.
- Anything else from the old repo (unresolved P0 decisions, the old coordination protocol, an AOKAI spec that was never located) is not inherited. If it becomes relevant to actual MVP scope, it gets raised fresh here.

## Current Status
- Migrated from `WebStaffr-clean`: engine, persistence, Angel worker, tests (54/54 passing), health check (HEALTHY).
- No auth, CI/CD, hosting, or production deployment decision made yet.
- No real credentials configured for GoHighLevel or Grok — `GrokVoiceBackend`/`GoHighLevelClient` remain `[Unverified]` against live accounts until exercised with real keys.
- The pytest-dependency and CORS-scoping fixes below were committed and pushed to `origin/main` (`3ca933b`) after founder approval.
- Backend intake endpoint now exists (`POST /intake`, see 2026-07-05 addendum below). Still outstanding: the actual Lovable-generated customer site and wiring the Angel widget into it.

### Session Addendum (2026-07-05) — state reconciliation

Re-verified every claim above against the actual code and a real test/health-check run (not just re-reading the docs):

- **Confirmed accurate, re-verified this session**: 54/54 tests pass, health check reports HEALTHY, `GoHighLevelClient`/`GrokVoiceBackend` implementations match the `[Unverified]`-against-live-account caveats in `CREDENTIALS.md` (code itself marks `update_appointment`/`cancel_appointment` as unverified), no `.env` or DB file committed, no hardcoded secrets found, `angel_prompt.md` and the Angel widget (`webstaffr/workers/angel/widget/angel-widget.js`) both exist and are real functional implementations (not stubs) — voice is honestly disabled in the UI rather than faked.
- **Confirmed accurate**: no intake-flow or Lovable-site code exists in this repo yet — the "Next" item above is still genuinely outstanding, not already started and forgotten.
- **Git**: local `main` and `origin/main` verified identical at `77da37a` (content-checked via `git ls-remote`, not just ahead/behind count).
- **New finding, not previously documented**: `requirements.txt` does not list `pytest`. Following the README's own local-dev steps verbatim (`pip install -r requirements.txt` then `pytest tests/`) fails with `ModuleNotFoundError` on a genuinely fresh environment unless `pytest` happens to already be installed globally. Either add `pytest` to `requirements.txt` (or a `requirements-dev.txt`) or update the README to call it out as a separate install step.
- **New finding, not previously documented**: `router.py`'s `CORSMiddleware` uses `allow_origins=["*"]` app-wide (see code comment at the call site acknowledging this is broader than intended "in spirit"). This currently makes `/book` and `/webhooks/ghl` — not just `/chat` — callable cross-origin from any site. Worth an explicit decision before any production exposure: scope CORS to `/chat` only (e.g. per-route middleware or a dependency-based origin check) or confirm wildcard is intentional for all three endpoints.

**Both findings above fixed same session (2026-07-05), approved directly by founder:**
- Added `requirements-dev.txt` (pinned `pytest==9.1.1`) and updated README's local-dev steps to install it alongside `requirements.txt`. This is a new dependency, approved explicitly in-session per the Self-Approval Scope rule above.
- Replaced the app-wide `CORSMiddleware` in `router.py` with `ScopedCORSMiddleware`, a small custom middleware restricted to `_CORS_SCOPED_PATHS = {"/chat"}`. `/book` and `/webhooks/ghl` no longer carry `Access-Control-Allow-Origin` headers. Added 4 regression tests (`TestCORSScoping`, plus a no-CORS check on `/health`) that assert this directly rather than relying on code review alone. Full suite re-run after the change: 58/58 passing (54 original + 4 new), health check still HEALTHY.
- Not yet done: committing and pushing these changes — pending explicit approval for the push step per CLAUDE.md's Self-Approval Scope (local commit is reversible/in-session; push to GitHub is not self-approvable).

**Update:** committed and pushed by founder same day. `origin/main` now at `3ca933b`. Verified directly (fetch + `git ls-remote`), not assumed.

### Session Addendum (2026-07-05) — intake flow (first slice of MVP scope)

Built the backend half of "intake" per the MVP scope above: `POST /intake`, a new `intake_submissions` table (migration `0003`), and `GET /intake/presets[/{industry}]`. Site generation itself is still out of scope here (Lovable's job per this doc's MVP Scope section).

**Provenance, not reinvention:** the field set (9 sections, ~35 fields) and required-field list are ported from the legacy `webstaff`/SiteSpin repo's proven intake form (`/Users/doc/Claude/Projects/WebStaffr/intake/intake.html`, read directly via Desktop Commander, not assumed from memory). That repo is a *different, older* codebase than this one — not `WebStaffr-clean` — reached only because the founder referenced two terms ("perfect site protocol," "malleable per-trade intake form") that turned out to be real, verifiable concepts there:

- **"Perfect-Site-Checklist"**: a data-integrity standard applied to that repo's site generator on 2026-07-04 — never fabricate reviews, testimonials, ratings, or credentials; render only real contractor-submitted data; omit a section rather than invent filler. Caught two real bugs there (a lead-capture form posting to a dead route; three hardcoded fake testimonials on every generated site). The full checklist document itself was never located — it's referenced as having lived in Google Drive, unresolved even in that repo's own status notes. What's real and reusable is the principle and its code-level effects, which is what got carried forward here.
- **Per-trade "malleable" intake**: correction to an assumption made mid-session — the old form does *not* use a different field schema per trade. All ~35 fields are the same for every industry. What varies per trade is presentation only: placeholder/example copy (`TRADE_HINTS`) and which field-service-management software options are offered (`INDUSTRY_SOFTWARE`, e.g. ServiceTitan/Jobber for HVAC vs. Vagaro/Mindbody for salons). Ported as-is into `webstaffr/trade_presets.py`.

**What was built:**
- `webstaffr/migrations/0003_intake_submissions.sql` — tenant-scoped table, same migration pattern as `0001`/`0002`.
- `webstaffr/intake.py` — `IntakeSubmission` dataclass, `IntakeRepository` (mirrors `booking.py`'s pattern), `generate_tenant_id()` (business-name slug + random suffix, since two businesses can share a name), `validate_intake_payload()` (required fields, plan enum, rating range).
- `webstaffr/trade_presets.py` — static per-industry hint/software config, presentation-layer only, no schema impact.
- `webstaffr/intake_router.py` — `POST /intake`, `GET /intake/presets`, `GET /intake/presets/{industry}`, mounted into the existing app via `include_router()` in `workers/angel/router.py` (kept that file's own router Angel-specific, per its existing docstring).
- CORS: `/intake` and `/intake/presets*` added to `ScopedCORSMiddleware`'s scoped paths (same reasoning as `/chat` — the intake form runs on an arbitrary origin), `Access-Control-Allow-Methods` extended to include `GET`.
- `tests/test_intake.py` — 15 new tests (submission success, tenant-id generation/uniqueness, full-row persistence, validation failures don't persist partial data, preset lookup/alias/fallback, CORS scoping).

**Verified this session:** full suite 73/73 passing (58 prior + 15 new), health check still HEALTHY. Manually exercised `/intake` and `/intake/presets` with `TestClient` before writing formal tests, confirming request/response shapes matched the design before locking them into assertions.

**Not yet done:** commit + push (same sandbox `.git/index.lock` limitation as the prior addendum — needs to run from the founder's own terminal), and the actual site-generation step (Lovable) that consumes this intake data.
