---
name: quality-review
description: Review a subagent's completed work before treating it as done, committing, or updating TASKS.md/CLAUDE.md. Use after every subagent-dispatch completes, whether from one subagent or several run in parallel.
---

# Quality Review

## What "done" actually requires

Never accept a subagent's own summary as proof of completion. Check, in this order:

1. **Test evidence, not test claims.** The subagent must show actual `python -m pytest tests/` output (or the specific file it touched) and `scripts/health_check.py` output from this session. "Tests pass" with no shown output is not verified — ask for the run, or run it yourself.
2. **Invariant compliance.** Spot-check the diff against the real rules, not the generic ones a fresh subagent might default to:
   - Raw SQL via `db.py`'s `get_connection()`, `?` placeholders — no SQLAlchemy/ORM introduced.
   - New integrations follow `Protocol` + `Null*` + real-impl, dependency-injected via constructor.
   - Every query is tenant-scoped.
   - CORS added only if the route is browser-facing (`/chat`, `/intake*`, `/sites/*`) — server-to-server routes (`/book`, `/webhooks/ghl`, `/retell/*`) get none.
   - Nothing assumes a persistent process or held-open connection (Vercel serverless).
   - No fabricated placeholder ratings/reviews/testimonials/credentials; any change to `site_data.py`'s public projection re-checked against the never-leak list (`lead_routing`, `approver`, `competitors`, `license_number`, ...).
3. **Secrets.** No secret value appears in the subagent's output, in a committed file, or in what it's asking you to relay to the founder. New env vars are named, not valued, and get `CREDENTIALS.md` + `README.md` + `.env.example` all updated together.
4. **Scope.** Did the subagent do exactly the dispatched sub-task, or did it wander into unrequested fixes? Flag scope creep even if the extra work looks good — log it in `TASKS.md` instead of silently accepting it.
5. **Approval boundary.** Did the subagent attempt (or recommend as already-done) a git push, deploy, or new dependency? Those need explicit founder approval regardless of how confident the subagent is — treat any such action as proposed, not executed, until you've surfaced it.

## Resolving conflicts across parallel subagents

If two subagents touched overlapping files or made incompatible assumptions (e.g. one assumed `sync_to_ghl=True` is now safe, another didn't), don't merge blindly — re-check the actual current repo state and reconcile by hand before accepting either.

## After review

- **Approved:** update `TASKS.md`, append a dated `CLAUDE.md` addendum (matching the existing style — what was built, what was verified this session, what's not yet done), local commit if warranted. Push only on separate, explicit founder go-ahead.
- **Not approved:** send it back to a fresh subagent dispatch with the specific gap, not a vague "try again."
