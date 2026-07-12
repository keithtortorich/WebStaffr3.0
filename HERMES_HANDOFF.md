# Hermes Handoff Plan — week of 2026-07-12

**Why this exists:** Claude Code's token budget for this week is nearly gone. Rather than stall, Hermes (already installed on this Mac, with existing skills at `~/.hermes/skills/webstaffr/webstaffr-analyze/` and `.../webstaffr-implement/`) takes over as the primary execution driver until the budget resets. This doc is the handoff — read it once, then work from `TASKS.md`/`CLAUDE.md` same as always.

## 1. Current project state, as of today (verify live, don't trust this doc by Wednesday)

- **MVP flow (intake → generated site → Angel widget) is fully verified end-to-end as of today.** Supabase `DATABASE_URL` authenticates in production, `/intake` and `/sites/{tenant_id}` work against the live Vercel backend, the Lovable "Site Weaver" frontend renders real data (required a build-time-secret fix, also done today), and `/chat` returns real Grok replies.
- **Open, not blocked:** Lovable UX polish, deleting the two throwaway diagnostic scripts once you're comfortable, general hardening.
- **Blocked on you, not technical:** GHL signup — you're deliberately holding off (30-day trial clock).
- **No decision made yet:** auth, CI/CD, production-readiness beyond what's in `CLAUDE.md`.

Full detail lives in `TASKS.md` (live status) and `CLAUDE.md`'s dated addenda (durable decisions/history) — same two files this session read first every time. Point Hermes at the same two files first, every session, before it does anything.

## 2. Before Hermes touches anything

The existing `~/.hermes/skills/webstaffr/*` skills were written 2026-07-08/07-12 and describe Supabase and `GROK_API_KEY` as blocked — that's stale as of today. Don't let Hermes work off its own skill file's cached "state" section. Either:
- Tell it explicitly at the start of every session to re-read `TASKS.md` + the last `CLAUDE.md` addendum live instead of trusting the skill's own summary, or
- Have it refresh those two skill files' "current state" sections once, pointing at today's addendum.

I didn't refresh those files myself this session — didn't want to spend more of this week's budget on it without you asking. Say the word if you want that done before I run out.

## 3. Rules that carry over unchanged — not Claude-specific, hold Hermes to the same bar

- **Never type, paste, or retrieve a real credential value into any agent session** — `DATABASE_URL`, `GROK_API_KEY`, any `GHL_*`/`RETELL_*` value. Same rule regardless of which agent is asking. `CREDENTIALS.md` stays names-only, no value, ever — no fallback-reads-a-committed-file tricks either (I removed exactly one of those today).
- **Hard gates always need your direct approval, from any agent:** git push, deploy, new dependency, architecture/data-model change, anything actually touching Lovable/Vercel/Supabase infrastructure (not just their credentials — the actions themselves).
- **Independently re-test any third-party agent's "fixed"/"verified" claim before trusting it.** This bit us for real today — Lovable's own AI agent reported a fix that turned out to be false on first re-check. Don't let that happen twice.
- **Perfect-site principle:** generated sites never fabricate reviews, ratings, or testimonials. Omit missing data, don't invent it.

## 4. What Hermes can self-approve this week

Per `CLAUDE.md`'s own Self-Approval Scope (applies to any agent, not just me): reversible local-only changes — code edits, tests, docs, refactors, best-practice improvements (auth, rate limits, error handling, test coverage) — as long as the test suite stays passing and `scripts/health_check.py` stays HEALTHY. No need to ask you for each one.

## 5. Suggested queue for the week, rough priority order

1. Lovable "Site Weaver" UX polish — the plumbing is done, this is now safe, self-contained work.
2. Delete `scripts/test_db_connection.py` and `scripts/build_database_url.py` once you're comfortable the Supabase connection is staying stable.
3. When you start the GHL trial: Hermes can prep the integration wiring code ahead of time, but you generate and set the actual `GHL_API_KEY`/`GHL_LOCATION_ID` yourself, same as every other credential so far.
4. Any further hardening Hermes finds — log it to `TASKS.md` as it's found, don't silently fix things without a record; that's how `CODE_REVIEW.md`'s items got tracked and closed out cleanly.

## 6. What NOT to hand to Hermes

- Account creation/signups — still you, deliberately.
- Anything that needs the Supabase or Lovable MCP tools this session used for direct live-state checks (DB table/row inspection, Lovable secret/build-config debugging). Confirm Hermes actually has equivalent tool access before assuming parity — if not, those specific checks wait for me.
- git push / Vercel deploy — Hermes stages and asks, you pull the trigger, same as always.

## 7. Reconciling when I'm back

Hermes logs to the same `TASKS.md`/`CLAUDE.md` this session used — dated addenda, terse `TASKS.md` lines, no separate log file. When budget resets, I read those same two files first, same as every session start today. No special handoff doc needed beyond this one plus whatever Hermes appends as it works.
