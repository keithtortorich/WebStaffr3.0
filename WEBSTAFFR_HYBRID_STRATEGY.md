# WebStaffr 3.0 — Hybrid Collaboration Notes (Cowork + Hermes)

**Status:** Draft/optional. This is tooling/orchestration, not on the
direct MVP path (intake → generated site → working Angel widget → live
voice). Added 2026-07-08 per founder request; not required reading to
continue MVP work — see `TASKS.md` for the actual next steps.

## Role split

- **Claude Cowork**: strategy, research, documentation, review, approval
  gate for git push / deploy / new dependencies / architecture changes.
- **Hermes Agent**: local execution — code, tests, iteration — inside the
  same guardrails (`webstaffr-mvp-guardrails` skill): scope gate, approval
  boundaries, invariants, verification-before-done.

Both should orient from `TASKS.md` + the last `CLAUDE.md` addendum, not
from this document or from memory.

## Model/cost note [Verified 2026-07-08]

Hermes' active model (`~/.hermes/config.yaml`) is
`stepfun/step-3.7-flash:free` via the Nous provider — already free-tier,
no switch needed today. See the `ensure-free-llm` skill
(`~/.hermes/skills/devops/ensure-free-llm/`) for how to re-check this and
for an optional local-Ollama upgrade path (removes network dependency
entirely; not yet built or tested).

## Skills added this session

| Skill | Purpose |
|---|---|
| `ensure-free-llm` | Check current model cost status, document upgrade path |
| `retell-ai-function-calling` | Reference for the already-built Retell integration — not a build plan |

## What this document deliberately does not do

It does not install Ollama, pull models, switch Hermes' active model, run
tests, or touch git. Those are new-dependency / execution actions that
need a separate, explicit go-ahead per the guardrails' approval
boundaries — see the `ensure-free-llm` skill for the exact commands if
that's wanted later.

## Open question for the founder

Given the scope gate above: is this hybrid-tooling work worth prioritizing
over the actual MVP blockers currently in `TASKS.md` (Supabase incident
recovery, GHL signup timing, Retell live-account wiring)? [Not decided —
flagging, not assuming.]
