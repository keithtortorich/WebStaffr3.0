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
- Next: intake flow and Lovable-generated customer site, then wiring the Angel widget into it.
