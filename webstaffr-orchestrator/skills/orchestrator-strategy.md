---
name: orchestrator-strategy
version: 1.0.0
description: Decompose a WebStaffr 3.0 task into delegatable sub-tasks for Hermes, gated by the same scope/approval rules as the webstaffr-mvp-guardrails skill. Use before any multi-step implementation or before dispatching work to Hermes subagents.
author: Cap'n (Keith Tortorich) + Claude
---

# Orchestrator Strategy for WebStaffr

## When to Use

- Starting any feature, fix, or CODE_REVIEW.md item that spans more than one file/concern.
- Before dispatching anything to Hermes via `subagent-dispatch`.
- Not for single-file, single-concern edits — just do those directly, no need to decompose.

## Step 1: Orient (cheap, mandatory — do this every time, don't trust memory)

Read `TASKS.md` and the **last dated addendum only** in `CLAUDE.md`. Never assert current state ("X is wired up", "Supabase incident cleared") from a status doc or from what a prior session claimed — verify against live code/tools this session, or label it `[Unverified]`.

## Step 2: Scope gate

Is this task on the shortest line to MVP (intake → generated site → working Angel widget → live voice)?

- **Yes** → proceed to Step 3.
- **No** → say so in one sentence and ask the founder before spending any delegation budget on it. (This is exactly the question `WEBSTAFFR_HYBRID_STRATEGY.md` left open about this orchestrator system itself — the founder has already answered it once for that case; don't assume the same answer applies to every future off-path request without asking again.)

One task per turn. Discovered side-issues get logged in `TASKS.md`, not fixed inline, unless trivially in-path.

## Step 3: Decompose into sub-tasks

Break the task into atomic, independent-as-possible pieces, e.g. "add `get_availability` to `/retell/function-call`":

- Sub-task A: handler in `webstaffr/workers/angel/retell_router.py`
- Sub-task B: any repository/query logic it needs (raw SQL via `webstaffr/db.py`, not an ORM)
- Sub-task C: `unittest` tests (success + failure path) in `tests/`
- Sub-task D: `TASKS.md` line + `CLAUDE.md` addendum

Not every task decomposes into all four — a doc-only fix might just be D.

## Step 4: Assign to Hermes

Use the `subagent-dispatch` skill to delegate each sub-task with full context. Hermes subagents start with zero memory of this conversation.

## Step 5: Review and synthesize

Use the `quality-review` skill on everything that comes back before treating it as done. Collect results, resolve conflicts, and only then update `TASKS.md`/`CLAUDE.md`.

## Success criteria

- All sub-tasks complete.
- Full suite (`python -m pytest tests/`) and `scripts/health_check.py` actually run and shown passing this session — not assumed from a prior claim.
- `TASKS.md` and a dated `CLAUDE.md` addendum updated.
- No regression, no unrequested follow-on work started.
- Local commit is fine (self-approvable); **push is not** — that needs explicit founder approval every time, not just once.
