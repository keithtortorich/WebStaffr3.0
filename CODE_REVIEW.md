# WebStaffr 3.0 — Code Review

Scope: `webstaffr/` package (routers, `intake.py`, `site_data.py`, `db.py`, `ghl.py`,
`voice.py`, `booking.py`, tenant/workflow/execution/executor engine, migrations),
`index.py`, `tests/`, `requirements.txt`/`requirements-dev.txt`, CORS middleware,
RLS migration. The Lovable "Site Weaver" frontend is out of scope. This review is
read-only — no source file was modified.

Every finding below was verified by reading the cited file/lines this session.
Where I'm inferring risk rather than having a confirmed exploit path, it's
labeled `[Inference]` per this repo's own epistemic convention (CLAUDE.md).
Findings already fixed and documented in CLAUDE.md (the `competitors` leak,
CORS scoping, DB-error-message leakage, RLS default-deny, `pytest` pin) were
re-verified against current code and are **not** re-reported as new issues;
where re-verification changed the picture (e.g. the RLS migration file itself),
that's called out explicitly.

---

## 1. Security Audit

Overall the backend follows disciplined patterns: every SQL query is
parameterized (no string-interpolated SQL was found anywhere), every
repository method takes `tenant_id` explicitly and scopes its `WHERE`
clause by it, the public site-data endpoint uses an allowlist (not a
denylist) of exposed fields, secrets are never hardcoded or committed, and
the previously-documented DB-error-leakage and cross-origin-scope bugs are
genuinely fixed. The most consequential gap is architectural rather than a
coding bug: there is no authentication anywhere, and two endpoints
(`/book`, `/webhooks/ghl`) rely on `tenant_id` as if it were a secret when
it is in fact public (returned to API callers and embedded in page source
via the widget's `data-tenant-id` attribute). With `GROK_API_KEY` now live
in production (per CLAUDE.md's 2026-07-08 addendum), this stops being a
theoretical gap the moment the Supabase outage clears.

### Findings

**[High] No authentication on any endpoint; `/book` and `/webhooks/ghl` treat a public value as a secret.**
`webstaffr/workers/angel/router.py:187-289` — `/chat`, `/book`, `/webhooks/ghl`,
and `intake_router.py`'s `/intake` all accept `tenant_id` as the only
scoping credential, with no API key, session, or HMAC signature required.
`tenant_id` is not secret: it is returned directly in `IntakeResponse`
(`intake_router.py:92-98`), used as a public URL segment for
`GET /sites/{tenant_id}` (`site_router.py:34`), and shipped in the visible
page source of every generated customer site via
`<script data-tenant-id="TENANT_ID">` (`angel-widget.js:6-9`, confirmed in
CLAUDE.md's Lovable-wiring addendum). Anyone who views a customer site's
page source, or fetches `GET /sites/{tenant_id}` for a guessed slug, can
then call `/book` to create arbitrary appointments for that tenant, or
`/webhooks/ghl` (see next finding) to trigger Angel — both are reachable
directly (curl, a script) regardless of CORS, since CORS is a
browser-only restriction and neither endpoint requires a browser.
`[Inference]`: exploitability is confirmed at the code level; I have not
attempted a live exploit against the deployed instance.

**[High] `/webhooks/ghl` has no signature/shared-secret verification — a forgeable webhook.**
`webstaffr/workers/angel/router.py:253-288`. `GHLWebhookEvent` is validated
only for shape (`tenant_id` regex, `event_type` in
`SUPPORTED_EVENT_TYPES`) — there is no check that the request actually
came from GoHighLevel (no HMAC header check, no shared secret, no IP
allowlist). Combined with the previous finding, any caller who knows a
`tenant_id` can POST a fabricated `website_lead`/`missed_call` event and
get `Angel.respond()` to run for that tenant — which, once `GROK_API_KEY`
is live (it now is, per CLAUDE.md), makes a real, billed xAI API call.
This is effectively an unauthenticated way to spend the founder's xAI
credits per tenant, with no rate limit (see next finding).

**[High] No rate limiting or payload-size limits on `/chat` / `/webhooks/ghl`, and `GROK_API_KEY` is now live in production.**
`webstaffr/workers/angel/router.py:187-205` (`ChatRequest.message: str`)
and `voice.py:97-112` (Grok call sends whatever `message` the caller
supplied, capped only by `max_tokens=500` on the *output*, not the input).
There is no `Field(max_length=...)` on `ChatRequest.message` or
`GHLWebhookEvent.message`, no per-tenant or per-IP request-rate limiting
anywhere in the app, and `/chat` is deliberately CORS-open to arbitrary
origins by design (any customer-site visitor must be able to call it).
Once the Supabase outage (TASKS.md, external, not a code bug) clears and
`/chat`/`/webhooks/ghl` stop 503'ing before reaching Grok, this becomes a
live, unauthenticated way to run up real xAI usage costs against a live
key with no cost ceiling. `[Inference]`: I did not measure actual token
costs; the absence of any length/rate control is directly verified.

**[Medium] `license_number` is exposed on the public `GET /sites/{tenant_id}` endpoint; not treated as internal despite Supabase's own advisory flagging it as sensitive.**
`webstaffr/site_data.py:37-49` — `license_number` is included in the
*mandatory* base dict returned by `build_public_site_data()`, unlike
`lead_routing`/`approver`/`competitors`/etc., which are correctly excluded
per the module's own docstring (`site_data.py:1-25`). CLAUDE.md's
2026-07-07 addendum records that Supabase's advisor tool flagged
`intake_submissions.license_number` as a `sensitive_columns_exposed`
warning at the database layer. That finding was about direct
anon-key/PostgREST access (not exploitable today since the app uses a
direct Postgres connection) — but this application-layer endpoint *does*
deliberately publish the same column to anyone who knows a `tenant_id`,
which is a separate, real exposure path the RLS fix didn't address.
`[Inference]`: contractor license numbers are commonly displayed on real
business websites as a trust signal, so this may well be intentional
product design rather than a bug — but given the DB-layer advisory
already called this column out as sensitive, it deserves an explicit
founder decision rather than being carried forward implicitly.
`has_gbp` (`site_data.py:51-67`) is a smaller, harmless gap in the
opposite direction — it's not internal-only per the docstring, but it's
also just missing from `optional_fields`, so it never renders; a
completeness bug, not a leak.

**[Medium] RLS migration (`0004_enable_rls_default_deny`) exists only in the live Supabase project, not as a file in this repo.**
`webstaffr/migrations/` contains only `0001_initial.sql`,
`0002_angel_appointments.sql`, `0003_intake_submissions.sql` — verified via
directory listing. CLAUDE.md's 2026-07-07 addendum describes applying
`0004_enable_rls_default_deny` directly via the Supabase MCP tool
(`apply_migration`), consistent with the documented design that Postgres
schema is managed out-of-band and this app's own `migrate()` is a no-op
under Postgres (`db.py:230-243`). That's a deliberate, documented tradeoff
for schema DDL in general — but RLS policy is a security control, and
right now it exists nowhere in version control. If the Supabase project
were ever recreated or migrated to a new region (the repo's own addenda
mention this as a live possibility given the `ap-south-1` incident), RLS
default-deny would not be reapplied unless someone manually remembers to
re-run it. `[Inference]`: this is a process/reproducibility risk, not a
currently-exploitable bug — `get_advisors` was reported clean as of the
last check.

**[Low] `GoHighLevelClient._request` includes the raw HTTP response body in exception messages, but this is confirmed contained to server-side logs, not leaked to clients.**
`webstaffr/workers/angel/ghl.py:100-101` —
`raise GHLSyncError(f"...{exc.read()}")`. Traced every call site: both
`Angel.book_appointment` (`angel.py:150-166`) and `Angel.log_note_to_ghl`
(`angel.py:169-186`) catch this broadly and only `logger.warning(...)` it
— it never propagates into an HTTP response. Noted as verified-clean
rather than a new finding, since the class of bug (raw backend errors
leaking to clients) was exactly what CLAUDE.md's 2026-07-07 addendum fixed
for the five DB-connection call sites; this confirms GHL errors follow the
same safe pattern.

**[Low] No SQL injection risk found anywhere in the codebase — verified explicitly given the custom Postgres compatibility shim.**
Every call site in `repository.py`, `booking.py`, `intake.py` uses `?`
placeholders with a separate `params` tuple; none of them build SQL by
string-concatenating request data. `db.py`'s `_PGConnection.execute()`
(`db.py:119-172`) rewrites *static* SQL text (`INSERT OR IGNORE` →
`ON CONFLICT DO NOTHING`, `?` → `%s`, appending `RETURNING <pk>`) — it
never touches or reformats the `params` tuple itself, so parameter values
still pass through psycopg2's own escaping. The one fragility worth
flagging (see Maintainability §2) is that the naive `text.replace("?",
"%s")` (`db.py:164`) would corrupt any future SQL containing a literal
`%` (e.g. a `LIKE '%foo%'` clause) — grepped the codebase for `LIKE`/`%`
usage in SQL strings and found none today, so this is not a live bug, but
it is a latent trap for the next contributor.

**[Info] Tenant isolation is correctly enforced at the persistence layer.**
Verified `WorkflowRepository.load` (`repository.py:59-85`),
`ExecutionRepository.load` (`repository.py:134-160`),
`IntakeRepository.load`/`load_latest_for_tenant`
(`intake.py:285-322`), and `AppointmentRepository` all include `tenant_id`
in every `WHERE` clause, and `WorkflowExecutor.run` additionally raises
`TenantScopeViolation` if a workflow's own tenant doesn't match the
caller's tenant (`executor.py:77-81`). `tests/test_repository.py`'s
`test_load_is_tenant_scoped` cases exercise this directly. No path was
found where one tenant's row is reachable via another tenant's ID or a
missing `WHERE` clause.

**[Info] CORS scoping matches CLAUDE.md's description and is correctly restrictive.**
`ScopedCORSMiddleware` (`router.py:102-124`) only attaches
`Access-Control-Allow-Origin` for `/chat`, `/intake`, `/intake/presets*`,
and `/sites/*`; `/book` and `/webhooks/ghl` carry no CORS headers,
confirmed by `tests/test_router.py`'s `TestCORSScoping`. `Access-Control-
Allow-Credentials` is never set, so the wildcard origin is not paired with
credentialed requests — a safe combination.

**[Info, `[Unverified]`] Dependency CVE assessment could not be performed with confidence.**
`requirements.txt` pins `fastapi==0.128.8`, `starlette==0.49.3`,
`pydantic==2.13.4`, `httpx==0.28.1`, `psycopg2-binary==2.9.12` — all dated
to mid-2026 per this session's `currentDate` context, which is beyond what
I can verify against a live vulnerability database from here. I did not
find any hardcoded-secret, unpinned (`>=`), or obviously abandoned
dependency. Recommend running `pip-audit` or `safety check` directly
against `requirements.txt` rather than trusting an assessment I can't
actually back with current CVE data — flagging this as a process gap
rather than asserting specific CVEs.

**[Info] Input validation completeness gaps (not exploitable today, but real gaps).**
`intake_router.py`'s `IntakeRequest` (`:29-89`) has no `max_length` on any
`str` field (`biz_name`, `notes`, `keywords`, etc.) and no max-item-count
on `services: list[str]` — a caller could submit an arbitrarily large
payload that gets persisted in full. `email: str` is not validated as an
email shape (Pydantic's `EmailStr` isn't used). None of this is currently
exploitable beyond storage bloat/DB bandwidth, since there's no rendering
of unescaped intake data anywhere (the widget uses `textContent`, verified
in `angel-widget.js:77`, and the Lovable frontend is out of scope) — but
it's a real completeness gap worth closing given `/intake` is an
unauthenticated, CORS-open, public endpoint.

---

## 2. Maintainability Review

The core domain layer (`tenant.py`, `workflow.py`, `execution.py`,
`executor.py`) is small, well-factored, and has strong test coverage. The
Angel/booking/GHL/voice layer follows a consistent
explicit-dependency-injection pattern that makes it genuinely testable
without live credentials. The main areas of accumulating risk are (a) the
Postgres compatibility shim in `db.py`, which is clever but has zero test
coverage against a real Postgres backend, and (b) small pockets of
duplicated connection-handling and tenant-upsert logic across the three
routers that predate `db.get_connection()`'s consolidation.

### Findings

**[Medium] The SQLite↔Postgres compatibility layer (`db.py:90-205`) has never been exercised by any test against a real Postgres connection.**
Confirmed by reading every test file (`tests/test_router.py`,
`test_intake.py`, `test_site_data.py`, `test_repository.py`,
`test_angel.py`, `test_executor.py`) — all of them construct SQLite
connections (`:memory:` or a temp file) via `connect()`/`create_app()`
with no `DATABASE_URL` set. `_PGConnection.execute()`'s three distinct
rewrite paths (the hardcoded `INSERT OR REPLACE INTO WORKFLOW_DEFINITIONS`
translation, the generic `INSERT OR IGNORE` → `ON CONFLICT DO NOTHING`
rewrite, and the `RETURNING <pk>` auto-append for `_LASTROWID_PK` tables)
have only ever been validated by (1) manual code review against
documented HighLevel/xAI-style vendor docs and (2) a smoke test against an
intentionally-unreachable `DATABASE_URL` that fails at the TCP/auth layer
before any of this rewrite logic runs (per CLAUDE.md's 2026-07-07
addendum: "confirmed it reaches a real `psycopg2.connect()` call and
fails with `OperationalError`"). This is a documented, deliberate tradeoff
(no local Postgres in the sandbox) — but it means the single most
dialect-sensitive piece of code in the repo is currently unverified by
anything except human review. `[Inference]`: I did not find a bug in this
logic by reading it, but "no test has ever run this code path" is itself
the risk, independent of whether a bug exists today.

**[Medium] Naive `text.replace("?", "%s")` in the Postgres shim is a latent fragility, not just a style nit (cross-referenced from §1).**
`db.py:164`. This works only because every SQL string in the codebase
today uses `?` exclusively as a bind-parameter marker and never contains a
literal `?` or `%` character in the query text itself (verified via
grep). The moment a future contributor adds a `LIKE '%' || ? || '%'`-style
query or any string containing a literal `%`, this shim will silently
either break (psycomg2 interprets stray `%` as a format specifier) or
produce a query with the wrong number of placeholders. There's no comment
at this line warning against that specific future change, though the
module docstring does explain the overall design.

**[Medium] Tenant-upsert SQL (`INSERT OR IGNORE INTO tenants ...`) is duplicated three times instead of reusing `repository.py`'s existing helper.**
`repository.py:25-28` defines `_ensure_tenant(conn, tenant_id)` and uses it
in `WorkflowRepository.save` and `ExecutionRepository.save`. But
`booking.py:36-38` (`AppointmentRepository.save`) and `intake.py:220-224`
(`IntakeRepository.save`) each re-inline the identical
`"INSERT OR IGNORE INTO tenants (tenant_id) VALUES (?)"` statement instead
of importing and calling `_ensure_tenant`. Functionally correct today, but
it's the same logic maintained in three places — a future change to how
tenant rows get upserted (e.g. adding an audit column) requires
remembering to update all three.

**[Low] Per-request DB connection open/commit/close is duplicated across three routers rather than reusing `db.connect()`'s existing context manager.**
`db.py:207-227` already implements exactly this pattern (open → yield →
commit-on-success / rollback-on-exception → always close) via
`connect()`. But `router.py`'s inner `get_connection()`
(`:172-181`), `intake_router.py`'s `_get_connection()` (`:100-111`), and
`site_router.py`'s `_get_connection()` (`:22-31`) each independently wrap
`db.get_connection()` (the raw factory, not the context manager) in their
own `try/except DB_ERRORS → HTTPException(503, "<slightly different
message>")`, and each request handler then hand-rolls its own
`try/finally: conn.close()` without an explicit `except: conn.rollback()`
branch (`router.py:196-202, 224-238, 267-281`; `intake_router.py:126-132`).
This isn't broken — for both SQLite and psycopg2, closing a connection
with an uncommitted transaction discards it — but it means the one place
that already got the commit/rollback/close contract right
(`db.connect()`) isn't the thing actually protecting the HTTP-facing code
paths.

**[Low] Dead/legacy content check: none found.** Grepped for commented-out
code blocks, unused imports, and orphaned functions across the reviewed
modules — none found. The `# noqa: BLE001` / `# noqa: F401` / `# noqa:
E402` comments throughout (`angel.py:70,158,179`, `router.py:323`,
`health_check.py` imports) are intentional, documented broad-exception or
import-order suppressions, not evidence of sloppy code.

**[Low] Docstring coverage is strong; a few thin spots.** Every module and
most non-trivial functions carry prose docstrings explaining *why*, not
just *what* — unusually thorough for a codebase this size. Thinner spots:
`webstaffr/db.py`'s `_PGCursor`/`_PGConnection` methods
(`fetchone`/`fetchall`/`commit`/`rollback`/`close`, `db.py:104-186`) have
no docstrings of their own (relying on the class-level docstring), and
`trade_presets.py`'s `TradeHint`/`TradeSoftware` `TypedDict`s have no
per-field documentation of what each key means (e.g. what distinguishes
`differentiator` from `tagline` isn't obvious without cross-referencing
`intake.py`).

**[Low] Test coverage gaps beyond the Postgres shim.** No test exercises:
`GoHighLevelClient._request`'s actual error-formatting behavior (only
`_request` itself is monkey-patched out in `test_angel.py:317-345`, so the
real `urllib`-based HTTP/error-handling code in `ghl.py:83-104` is never
exercised, mocked or otherwise); `sanitize_slug`/`generate_tenant_id`
edge cases directly (e.g. an all-symbols business name falling back to
`"client"`) — only indirectly via one HTTP round trip in
`test_intake.py:47-53`; and an actual OPTIONS preflight request against
`ScopedCORSMiddleware` (`router.py:114-115`'s early-return branch for
`scoped and request.method == "OPTIONS"` is untested).

---

## 3. Styling Audit

The codebase is stylistically consistent — 4-space indentation, double
quotes throughout, `snake_case` functions/variables, `PascalCase`
classes, `from __future__ import annotations` at the top of every module,
and type hints on essentially every function signature I read. This
consistency appears to be maintained by convention/discipline rather than
tooling: there is no linter, formatter, or type-checker configuration
anywhere in the repo.

### Findings

**[Medium] No linter/formatter/type-checker configuration exists in the repo.**
Checked for `pyproject.toml`, `setup.cfg`, `.flake8`, `ruff.toml`,
`mypy.ini`, `.pre-commit-config.yaml` — none present (confirmed via glob;
`pyproject.toml` was in fact deliberately *removed* per CLAUDE.md's
2026-07-07 addendum, because a bare `[tool.vercel]`-only `pyproject.toml`
broke the Vercel build). The `# noqa: BLE001`/`# noqa: F401`/`# noqa:
E402` comments scattered through the codebase (rule codes from
flake8-bugbear and pyflakes) imply an intent to run a linter that
recognizes those codes, but nothing in the repo actually runs or enforces
one — style consistency currently depends entirely on manual discipline,
which has held up well so far but has no backstop as the codebase grows
or if a second contributor joins.

**[Low] Consistent but unconventional docstring style relative to PEP 257.**
Docstrings throughout favor multi-paragraph prose explaining design
rationale (e.g. `db.py:1-26`, `site_data.py:1-25`) rather than the
terser imperative-summary-line-plus-Args/Returns shape PEP 257 and tools
like `pydocstyle`/Google/NumPy docstring conventions expect. This is
applied consistently across the whole codebase (a deliberate style choice,
not drift), so it's not a bug — but it means a `pydocstyle`/`ruff
--select D` check would flag nearly every docstring in the repo if ever
turned on, which is worth knowing before adopting one.

**[Low] Type hint coverage is high but not complete.** Nearly every
function signature has parameter and return type hints (`-> dict`, `->
Optional[int]`, etc.). Exceptions found: `_PGCursor.__init__`
(`db.py:100-102`) types `raw_cursor` implicitly as untyped `Any`-shaped
(no annotation on the parameter itself, only on `lastrowid`); test files
(`tests/*.py`) have no type hints anywhere, which is normal/acceptable for
unittest-style test code and not flagged as a real gap.

**[Low] Minor PEP 8 nits, no violations that affect readability.** Line
lengths in `trade_presets.py`'s `TRADE_SOFTWARE`/`TRADE_HINTS` dict
literals (`:59-163`) regularly exceed 100 characters (e.g.
`trade_presets.py:153`, a single-line dict entry well past 200 chars) —
consistent within that file (data-table-shaped, deliberately compact) but
would fail a default 79- or 99-character line-length lint rule if one were
ever added.

---

## Prioritized Action List

1. **[High, Security]** Decide and implement an auth story (even a
   minimal shared-secret/API-key header) for `/book` and especially
   `/webhooks/ghl` before the Supabase outage clears and these become
   reachable in production — right now `tenant_id` is being used as a
   de facto credential even though it's public. (`router.py:187-289`)
2. **[High, Security]** Add HMAC/shared-secret verification to
   `/webhooks/ghl`, and add a `max_length` on `ChatRequest.message` /
   `GHLWebhookEvent.message` plus some form of per-tenant rate limiting
   on `/chat` before relying on the now-live `GROK_API_KEY` in
   production — otherwise this is an open, unauthenticated way to spend
   real xAI credits. (`router.py:253-288`, `voice.py:97-112`)
3. **[Medium, Security]** Get an explicit founder decision on whether
   `license_number` should be public via `GET /sites/{tenant_id}` —
   Supabase's own advisor already flagged this column as sensitive at the
   DB layer; right now the application layer publishes it regardless.
   (`site_data.py:37-49`)
4. **[Medium, Security/Maintainability]** Commit the RLS
   `0004_enable_rls_default_deny` migration as a real file in
   `webstaffr/migrations/` (even if it stays a manually-applied Supabase
   migration rather than one `migrate()` runs) so RLS default-deny isn't
   solely dependent on institutional memory if the Supabase project is
   ever recreated or moved.
5. **[Medium, Maintainability]** Add at least one integration-style test
   that exercises `_PGConnection`'s actual query-rewriting logic (the
   `INSERT OR IGNORE`, `INSERT OR REPLACE`, and `RETURNING` paths in
   `db.py:119-172`) — even a unit test against a fake/mock psycopg2
   cursor that asserts the *rewritten SQL text* would catch a regression
   in the one piece of dialect-translation code nothing currently
   verifies.
