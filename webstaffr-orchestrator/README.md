# webstaffr-orchestrator

**Status:** Non-MVP tooling, built 2026-07-08 at the founder's explicit request (resolves the open scope question `WEBSTAFFR_HYBRID_STRATEGY.md` left flagged: "is this hybrid-tooling work worth prioritizing over the actual MVP blockers" — founder answered "build it now" when asked directly). Not required reading to continue MVP work; see `TASKS.md`.

## What this is

The Claude Cowork half of the two-layer setup described in `WEBSTAFFR_HYBRID_STRATEGY.md`:

- **This plugin (Cowork):** decomposes a task, delegates the execution pieces to Hermes, reviews what comes back, and holds the approval gate for git push / deploy / new dependencies / architecture changes.
- **Hermes (local execution):** the `webstaffr-analyze` and `webstaffr-implement` skills at `~/.hermes/skills/webstaffr/` on the founder's Mac, plus the existing `ensure-free-llm` and `retell-ai-function-calling` skills already documented in `WEBSTAFFR_HYBRID_STRATEGY.md`.

Both sides run inside the same rules as the `webstaffr-mvp-guardrails` skill — this plugin doesn't define a separate rule set, it operationalizes the existing one for a multi-agent workflow.

## Why it lives in this repo, not `~/.claude/plugins/`

The original design sketch put this at `~/.claude/plugins/webstaffr-orchestrator/`. Cowork's directory-mount system treats `~/.claude/plugins` as a protected host location and won't mount it — so instead of trying to route around that guard, this plugin lives in-repo at the root, the same way `marketing-director-gtm/` already does (see that folder's `cowork.plugin.json` for the precedent this one mirrors). Copy or symlink it to `~/.claude/plugins/webstaffr-orchestrator/` by hand if you want it auto-loaded outside this repo — that's a one-time step for you to do, not something done automatically here.

## Layout

```
webstaffr-orchestrator/
├── cowork.plugin.json
├── README.md
├── skills/
│   ├── orchestrator-strategy.md   # task decomposition, scope gate
│   ├── subagent-dispatch.md       # how to delegate to Hermes with full context
│   └── quality-review.md          # review Hermes' output before approving
└── agents/
    ├── backend-specialist.md      # webstaffr/ FastAPI backend, raw-SQL invariants
    ├── integration-specialist.md  # Retell / GHL / Supabase / Grok state
    ├── test-engineer.md           # pytest + health_check.py verification
    └── documentation-writer.md    # TASKS.md / CLAUDE.md / CREDENTIALS.md updates
```

## Corrections made vs. the original design doc

The doc this was built from was a generic template and got a few real project facts wrong. Fixed here, not carried forward:

- No SQLAlchemy, no ORM, no classic OOP repository layer — raw SQL via `webstaffr/db.py`'s `get_connection()`, `?` placeholders, wrapped in `DB_ERRORS`. `AppointmentRepository` (`webstaffr/workers/angel/booking.py`) exists but talks to the DB this way, not via an ORM.
- Integrations follow the `Protocol` + `Null*` safe-default + real-impl pattern already established for Retell/GHL/voice — not a generic "API client" shape.
- Test suite is `unittest` + `TestClient(app)` against temp-file SQLite (never `:memory:`), currently 121/121 passing, plus `scripts/health_check.py` — not a bare `pytest tests/ -v` with no further context.
- Retell is done and live (commit `1705b71`); GHL is blocked on the founder's own trial-timing decision, not a technical blocker; Supabase is blocked on an external platform incident. The original doc's "pending"/"in progress" labels were stale even at the time it was written.
