---
name: orchestrator-strategy
description: Decompose a WebStaffr 3.0 task into delegatable sub-tasks for Claude Code subagents, gated by the same scope/approval rules as the webstaffr-mvp-guardrails skill. Use before any multi-step implementation or before dispatching work to backend-specialist, integration-specialist, test-engineer, or documentation-writer.
---

# Orchestrator Strategy for WebStaffr

## When to Use

- Starting any feature, fix, or CODE_REVIEW.md item that spans more than one file/concern.
- Before dispatching anything via `subagent-dispatch`.
- Not for single-file, single-concern edits — just do those directly, no need to decompose.

## Step 1: Orient (cheap, mandatory — do this every time, don't trust memory)

Read `TASKS.md` and the **last dated addendum only** in `CLAUDE.md`. Never assert current state ("X is wired up", "Supabase incident cleared") from a status doc or from what a prior session claimed — verify against live code/tools this session, or label it `[Unverified]`.

## Step 2: Scope gate

Is this task on the shortest line to MVP (intake → generated site → working Angel widget → live voice)?

- **Yes** → proceed to Step 3.
- **No** → say so in one sentence and ask the founder before spending any effort on it. This orchestrator system itself is an example of off-path tooling the founder explicitly approved twice (2026-07-08 sketch, 2026-07-12 build, 2026-07-12 Cowork→Claude Code rework) — each time by being asked directly. Don't assume a standing "yes" for the next off-path request either; ask again.

One task per turn. Discovered side-issues get logged in `TASKS.md`, not fixed inline, unless trivially in-path.

## Step 3: Decompose into sub-tasks

Break the task into atomic, independent-as-possible pieces, e.g. "add `get_availability` to `/retell/function-call`":

- Sub-task A: handler in `webstaffr/workers/angel/retell_router.py`
- Sub-task B: any repository/query logic it needs (raw SQL via `webstaffr/db.py`, not an ORM)
- Sub-task C: `unittest` tests (success + failure path) in `tests/`
- Sub-task D: `TASKS.md` line + `CLAUDE.md` addendum

Not every task decomposes into all four — a doc-only fix might just be D.

## Step 4: Dispatch to a subagent

Use the `subagent-dispatch` skill to delegate each sub-task with full context to the matching project subagent (`backend-specialist`, `integration-specialist`, `test-engineer`, `documentation-writer` — defined in `.claude/agents/`). Subagents run in their own context window and start with zero memory of this conversation.

## Step 5: Review and synthesize

Use the `quality-review` skill on everything that comes back before treating it as done. Collect results, resolve conflicts, and only then update `TASKS.md`/`CLAUDE.md`.

## Success criteria

- All sub-tasks complete.
- Full suite (`python -m pytest tests/`) and `scripts/health_check.py` actually run and shown passing this session — not assumed from a prior claim.
- `TASKS.md` and a dated `CLAUDE.md` addendum updated.
- No regression, no unrequested follow-on work started.
- Local commit is fine (self-approvable); **push is not** — that needs explicit founder approval every time, not just once.
