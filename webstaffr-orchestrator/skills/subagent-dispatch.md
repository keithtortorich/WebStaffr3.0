---
name: subagent-dispatch
version: 1.0.0
description: Delegate a WebStaffr 3.0 sub-task to a Hermes subagent with complete, self-contained context. Use after orchestrator-strategy has decomposed a task, whenever execution should happen via Hermes rather than inline in this Cowork session.
author: Cap'n (Keith Tortorich) + Claude
---

# Subagent Dispatch

## Critical rule: provide complete context

Hermes subagents start with a fresh conversation — they know nothing that happened in this Cowork session. Every dispatch must include:

- Exact file paths (this repo's real layout, not guessed ones — e.g. `webstaffr/workers/angel/retell_router.py`, not `webstaffr/repositories/appointment_repository.py`, which doesn't exist).
- Any error messages, if this is a fix.
- The specific project invariants that apply (see `agents/backend-specialist.md` etc. for the actual list — don't restate a generic FastAPI/SQLAlchemy pattern that doesn't match this repo).
- Constraints (self-approvable vs. needs-founder-approval, per `webstaffr-mvp-guardrails`).
- What to return.

## Delegation template

> "Hermes, delegate_task to a fresh subagent with:
>
> **Goal:** [clear, specific goal]
>
> **Context:**
> - Project at: `/Users/doc/Desktop/WebStaffr 3.0`
> - Orient first: read `TASKS.md` + the last dated `CLAUDE.md` addendum — don't assume prior state.
> - Files involved: [list specific files]
> - What to do: [step-by-step]
> - Invariants: raw SQL via `webstaffr/db.py` `get_connection()` (no ORM), `Protocol`+`Null*`+real-impl pattern for integrations, every query tenant-scoped, CORS only on browser-facing routes, Vercel serverless (no persistent-process assumptions), no fabricated placeholder content.
> - Approval boundary: local edits + local commit are self-approvable; git push / deploy / new dependency / architecture change are NOT — flag and stop, don't do them.
> - Expected output: [what to return]
>
> **Tools:** terminal, file
>
> **Return:** structured summary — what was done, files touched, test results (must show the actual pass/fail output, not a claim), and anything flagged for founder approval."

## Parallel delegation

For genuinely independent sub-tasks, delegate together, capped at 3 concurrent (`~/.hermes/config.yaml`'s `max_spawn_depth`/`subagent_auto_approve: false` already enforces that subagent actions need approval — this cap is about not overwhelming review, not a hard technical ceiling):

> "Hermes, delegate_task in parallel for:
>
> Task 1: [...]
> Task 2: [...]
> Task 3: [...]"

Don't parallelize tasks that touch the same file (e.g. two handlers in the same router) — sequence those instead to avoid merge conflicts in a subagent's working copy.

## What NOT to delegate

- Anything requiring a secret (`GROK_API_KEY`, `DATABASE_URL`, etc.) to be typed into the session — that's a founder-only action per this project's Security Baseline, regardless of which agent is asking.
- git push, deploy, or a new dependency — Hermes subagents can *propose* these, but execution needs the founder's explicit approval, surfaced back through this orchestrator, not auto-run.
