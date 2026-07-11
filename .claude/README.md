# WebStaffr 3.0 — Claude Code project configuration

**Status:** Non-MVP tooling. Rebuilt 2026-07-12 (same session as the original build) at the founder's explicit request, switching the orchestrator system from a Claude Cowork + Hermes hybrid to native Claude Code. Not required reading to continue MVP work; see `TASKS.md`.

## What this is

Project-scoped Claude Code configuration for WebStaffr 3.0: four subagents (`agents/`) and three orchestration skills (`skills/`) that decompose a task, delegate execution pieces to the right specialist subagent, and hold the same approval gate (git push / deploy / new dependency / architecture changes) as the `webstaffr-mvp-guardrails` skill.

Everything here runs inside the same rules as `webstaffr-mvp-guardrails` — it doesn't define a separate rule set, it operationalizes the existing one for a multi-agent workflow, entirely within the `claude` CLI running locally.

## Why this replaced the Cowork + Hermes version

The system built on 2026-07-12 split strategist/orchestrator (Claude Cowork) from local execution (Hermes skills on the founder's Mac). The founder asked, later the same day, to collapse this to Claude Code only. Reasons this is a better fit, not just a different tool:

- **No cross-process handoff.** The Cowork/Hermes version required phrasing a `delegate_task` call to a separate gateway process and trusting it round-tripped context correctly. Claude Code's subagents are native — `Task`-tool delegation to a `.claude/agents/*.md` definition, in the same session, no external process.
- **No protected-path workaround needed.** The original design wanted `~/.claude/plugins/webstaffr-orchestrator/` for auto-load; Cowork's directory-mount system refused to mount that path, forcing an in-repo `cowork.plugin.json` workaround (see `webstaffr-orchestrator/README.md`, kept for history). Running via the real `claude` CLI on the founder's own Mac has no such restriction — but rather than fight the full plugin/marketplace system either, this uses Claude Code's simpler, documented, zero-install mechanism for exactly this case: **project subagents** (`.claude/agents/`) and **project skills** (`.claude/skills/<name>/SKILL.md`), auto-discovered the moment `claude` is run from this repo, no manifest or install step required. [Verified against `code.claude.com/docs/en/sub-agents` and `.../plugins-reference`, 2026-07-12.]
- **One less moving part to keep synchronized.** The Hermes skills (`webstaffr-analyze`, `webstaffr-implement` at `~/.hermes/skills/webstaffr/`) and this repo's invariants could drift out of sync across sessions. A single project config, checked into this repo's own git history, can't drift from itself.

## Layout

```
.claude/
├── README.md                        # this file
├── agents/
│   ├── backend-specialist.md        # webstaffr/ FastAPI backend, raw-SQL invariants
│   ├── integration-specialist.md    # Retell / GHL / Supabase / Grok state
│   ├── test-engineer.md             # pytest + health_check.py verification
│   └── documentation-writer.md      # TASKS.md / CLAUDE.md / CREDENTIALS.md updates
└── skills/
    ├── orchestrator-strategy/SKILL.md   # task decomposition, scope gate
    ├── subagent-dispatch/SKILL.md       # how to delegate to a subagent with full context
    └── quality-review/SKILL.md          # review a subagent's output before approving
```

Each agent file's frontmatter (`name`, `description`, `tools`, `model`) follows Claude Code's real subagent schema — `tools` lists actual Claude Code tool names (`Read`, `Write`, `Edit`, `Bash`, `Grep`, `Glob`, plus `WebFetch`/`WebSearch` for `integration-specialist`), not the Hermes-style `terminal, file, web` shorthand the prior version used.

## How to use it

From a terminal, run `claude` from this repo's root (`/Users/doc/Desktop/WebStaffr 3.0`). Claude Code auto-discovers `.claude/agents/` and `.claude/skills/` with no further setup. Then either:

- Let Claude delegate automatically when a task matches an agent's `description`, or
- Ask explicitly: "Use the backend-specialist agent to ..." — more reliable once a task has already been decomposed into named pieces (see `skills/orchestrator-strategy/SKILL.md`).

## What happened to `webstaffr-orchestrator/` (the Cowork plugin)

Left in place at the repo root, not deleted — this project's convention is to preserve history rather than silently rewrite it (same reasoning `CLAUDE.md` itself follows as an append-only log). Its `README.md` now carries a superseded notice pointing here. If it's never going to be used again, deleting it is a founder call, not made here.

The corresponding Hermes skill folders on the founder's Mac (`~/.hermes/skills/webstaffr/webstaffr-analyze/`, `.../webstaffr-implement/`) were **not touched** — that's outside this repo, on a real, actively-used Hermes install, and removing files there wasn't asked for. They're simply unused now; cleaning them up (or not) is the founder's call whenever convenient.

## Corrections carried forward from the original build (still accurate, restated here)

- No SQLAlchemy, no ORM, no classic OOP repository layer — raw SQL via `webstaffr/db.py`'s `get_connection()`, `?` placeholders, wrapped in `DB_ERRORS`.
- Integrations follow the `Protocol` + `Null*` safe-default + real-impl pattern already established for Retell/GHL/voice.
- Test suite is `unittest` + `TestClient(app)` against temp-file SQLite (never `:memory:`), last independently verified 136/136 passing (2026-07-08) — re-verify, don't repeat that number as current fact.
- Retell is done and live (commit `1705b71`); GHL is blocked on the founder's own trial-timing decision; Supabase was blocked on an external platform incident — check current status rather than trusting any prior session's claim.
