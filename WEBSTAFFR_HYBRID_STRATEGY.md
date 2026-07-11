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

## Model/cost note [Verified 2026-07-12, supersedes the 2026-07-08 note below]

`~/.hermes/config.yaml`'s active model is now `qwen2.5:14b` via a local
Ollama server (`provider: custom`, `base_url: http://localhost:11434/v1`),
confirmed live this session (`ollama list` shows the model pulled,
`ollama --version`/`api/version` responds). This is the local-Ollama
upgrade path the 2026-07-08 note below flagged as "not yet built or
tested" — it's since been done (a backup file,
`config.yaml.bak.pre_ollama_20260611_164746`, marks when the switch
happened). Zero per-token cost, no network dependency on a hosted
provider for Hermes' primary model. The `ensure-free-llm` skill's
stepfun/Nous description is stale as of this finding — re-check that
skill's own content before trusting it, same class of doc-drift this
repo has hit before.

## Prior note [Verified 2026-07-08, superseded above]

Hermes' active model was `stepfun/step-3.7-flash:free` via the Nous
provider — already free-tier, no switch needed at the time. See the
`ensure-free-llm` skill (`~/.hermes/skills/devops/ensure-free-llm/`) for
the original re-check procedure.

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
