---
name: subagent-dispatch
description: Delegate a WebStaffr 3.0 sub-task to a project subagent (backend-specialist, integration-specialist, test-engineer, documentation-writer) with complete, self-contained context. Use after orchestrator-strategy has decomposed a task, whenever execution should happen via a dedicated subagent rather than inline in the main conversation.
---

# Subagent Dispatch

## Critical rule: provide complete context

Each subagent runs in its own context window — it starts fresh, with no memory of what happened in the parent conversation. Every dispatch must include:

- Exact file paths (this repo's real layout, not guessed ones — e.g. `webstaffr/workers/angel/retell_router.py`, not `webstaffr/repositories/appointment_repository.py`, which doesn't exist).
- Any error messages, if this is a fix.
- The specific project invariants that apply (see `.claude/agents/backend-specialist.md` etc. for the actual list — don't restate a generic FastAPI/SQLAlchemy pattern that doesn't match this repo).
- Constraints (self-approvable vs. needs-founder-approval, per `webstaffr-mvp-guardrails`).
- What to return.

## How dispatch actually works in Claude Code

Claude Code delegates to a subagent in one of two ways:

- **Automatic:** Claude matches the task at hand against each subagent's `description` frontmatter and delegates on its own when there's a clear match.
- **Explicit:** ask directly, e.g. "Use the backend-specialist agent to add `get_availability` to `/retell/function-call`." This is the more reliable path when you (the orchestrating session) have already decomposed the work and know exactly which specialist should take which piece — don't rely on auto-matching for a multi-part decomposition, name the agent explicitly for each sub-task.

There is no separate "gateway" process to address (no Hermes-style `delegate_task` call) — the dispatch *is* the request to use a named agent, phrased with the full context below.

## Dispatch template

> "Use the **[backend-specialist | integration-specialist | test-engineer | documentation-writer]** agent to:
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
> **Return:** structured summary — what was done, files touched, test results (must show the actual pass/fail output, not a claim), and anything flagged for founder approval."

## Parallel delegation

Claude Code can run multiple subagents concurrently within a session. For genuinely independent sub-tasks, dispatch them together; keep the batch small enough that you can actually review each result carefully rather than rubber-stamping — there's no documented hard concurrency ceiling to rely on here, so use judgment over a fixed number.

Don't parallelize tasks that touch the same file (e.g. two handlers in the same router) — sequence those instead to avoid one subagent's edit clobbering another's.

## What NOT to delegate

- Anything requiring a secret (`GROK_API_KEY`, `DATABASE_URL`, etc.) to be typed into the session — that's a founder-only action per this project's Security Baseline, regardless of which agent is asking.
- git push, deploy, or a new dependency — a subagent can *propose* these, but execution needs the founder's explicit approval, surfaced back through the parent conversation, not auto-run.
