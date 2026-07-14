# ServiceTitan Integration — Recommended Scaffold
## WebStaffr 3.0
## Date: 2026-07-14

This document records the current shape of `webstaffr/integrations/servicetitan/`,
what still needs wiring to be complete, and the concrete file/test scaffold
to add next in a reversible, non-breaking way. No router wiring is proposed
in this scaffold; see the "Allowed router additions" gating note below.



## Current confirmed state as of 2026-07-14

```text
webstaffr/integrations/
    __init__.py
    servicetitan/
        __init__.py        exports: ServiceTitanClient, NotConfigured/Config/HTTP
                           errors, ServiceTitanSync, SyncResult, MockServiceTitanClient
        client.py          stdlib-urllib OAuth2 client, 9 read-first resource methods
        sync.py            bounded sync across 9 resource types; isolated failure
        mocks.py           MockServiceTitanClient seeded by resource key
tests/test_servicetitan.py
    ClientConstructionTests
    ClientHTTPTests
    MockServiceTitanClientTests
    ServiceTitanSyncTests
    ServiceTitanPollEndpointTests (optional; requires fastapi)
```

ServiceTitan is wired behind `SERVICETITAN_ENABLED=true` plus missing-secret
guardrails in `webstaffr/workers/angel/router.py`, but not yet exposed
through any tenant-aware workflow (`Angel`, GHL sync, retell handoff, etc.).



## Missing pieces to a complete integration

These are scoped as docs/test work + optional reversible local-only additions only.

- `CREDENTIALS.md` does not mention the four `SERVICETITAN_*` env vars.
  This is a real doc gap, not an opinion call. Covers failure behavior of
  the client when any one is unset: `ServiceTitanNotConfiguredError` is
  raised at construction time, never silently no-op (same convention as
  `GHLNotConfiguredError` / `GROK_API_KEY`/`NullVoiceBackend`).
- Router wiring for service-account polling is present; next step is needed:
  add provider-agnostic tenant-to-ServiceTitan mapping (no DB/schema change
  requested here), before any tenant-specific webhook would mean anything.
- Tests don't yet cover router registration path or provider configration
  truth tables.



## Recommended local-only additions (reversible; no push/deploy)

### 1) CREDENTIALS.md additions (reversible doc edit)

Add this section under a new `### 6. ServiceTitan ...`

```
### 6. `SERVICETITAN_CLIENT_ID` + `SERVICETITAN_CLIENT_SECRET` + `SERVICETITAN_TENANT_ID` (+ optional `SERVICETITAN_BASE_URL`)
- Purpose: read-first polling of jobs, customers, appointments, invoices,
  payments, locations, projects, installed equipment, and technicians.
- Behavior:
  - All three required vars set -> `webstaffr/integrations/servicetitan/client.py`
    builds a real `ServiceTitanClient`. Missing any one raises
    `ServiceTitanNotConfiguredError` at construction time; the
    `/integrations/servicetitan/poll` endpoint surfaces this as a `503`.
- Status: client and sync logic are implemented and have offline unit tests in
  `tests/test_servicetitan.py`. The polling endpoint is behind
  `SERVICETITAN_ENABLED=true` in `router.py`; no live ServiceTitan account has
  been exercised yet. Endpoint paths/payload shapes are `[Unverified]` against
  a live ServiceTitan tenant until exercised with real credentials.
- Security: never commit. Same as above.
```

This is the only required doc change to get the repository text in sync with
the actual env var names used by the integration.

### 2) TASKS.md additions (reversible doc edit)

Under the MVP core flow section, append:

```
- #33 — ServiceTitan integration scaffold created (2026-07-14):
  `webstaffr/integrations/servicetitan/` implemented with client, sync,
  mocks, and offline tests in `tests/test_servicetitan.py`. Integration is
  behind `SERVICETITAN_ENABLED=true` in the router, with missing-secret
  503s. Pending: `CREDENTIALS.md` env var documentation, provider-agnostic
  tenant-to-ServiceTitan mapping wiring, and live testing against real
  credentials. No DB schema change, no router wiring, no push.
```

### 3) Allowed router additions (not yet implemented; explicit gates)

The polling endpoint already exists (conditional on `SERVICETITAN_ENABLED`).
If/when the founder approves the following gates, the shape would be:

**Endpoint shape**

```python
@app.post("/integrations/servicetitan/poll")
def servicetitan_poll() -> dict:
    """Bounded read from ServiceTitan.

    Available only when `SERVICETITAN_ENABLED=true` and the client is
    configured; otherwise returns 503 with `ServiceTitanNotConfiguredError`
    detail. No new dependency. No new route-level CORS exposure.
    """
    try:
        from ...integrations.servicetitan import (
            ServiceTitanClient,
            ServiceTitanNotConfiguredError,
            ServiceTitanSync,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    try:
        client = ServiceTitanClient()
    except ServiceTitanNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    sync = ServiceTitanSync(client)
    return {
        "results": [
            {
                "resource": result.resource,
                "fetched": result.fetched,
                "failed": result.failed,
                "error": result.error,
            }
            for result in sync.run()
        ]
    }
```

This is identical to what already exists in `router.py` today under the
`SERVICETITAN_ENABLED` guard. The file currently uses this exact shape.

**Auth/secret warning**
`/integrations/servicetitan/poll` is an internal/operational route. If this
ever becomes browser-callable, add auth just like `/book` and `/webhooks/ghl`.
That is not approved here.

**Tenant mapping**
Do not add phone-number/tenant mapping in this cycle. That is new schema,
which requires explicit approval per plan hard gates.



## Recommended test matrix (commands and expected results)

Run any one of:

```bash
python3 -m unittest tests.test_servicetitan -v
python3 -m unittest discover -s tests -p "test_servicetitan.py" -v
```

Expected output with existing env cleared of `SERVICETITAN_*`:

```text
test_constructs_from_env ... ok
test_defaults_use_constructor_args_over_env ... ok
test_empty_by_default ... ok
test_failure_path ... ok
test_happy_path ... ok
test_http_error_surfaces_as_expected ... ok
test_returns_404_when_disabled ... skipped 'fastapi not installed'
test_returns_503_when_not_configured ... skipped 'fastapi not installed'
test_returns_seeded_records ... ok
test_isolated_failure ... ok
test_request_sends_bearer_and_oauth_payload ... ok
test_returns_structured_results ... skipped 'fastapi not installed'

----------------------------------------------------------------------
Ran 13 tests in 0.006s

OK (skipped=3)
```

When `fastapi` is installed in the resolved Python environment, the three
skipped tests should execute and pass; the 10 core offline tests never need
`fastapi`.

To verify the offline tests in isolation without any router involvement:

```bash
python3 -m unittest tests.test_servicetitan.MockServiceTitanClientTests \
                   tests.test_servicetitan.ServiceTitanClientConstructionTests \
                   tests.test_servicetitan.ServiceTitanClientHTTPTests \
                   tests.test_servicetitan.ServiceTitanSyncTests -v
```

Expected output:

```text
...
Ran 10 tests in 0.006s
OK
```



## What stays out of scope for this cycle

- No new dependency.
- No DB schema change.
- No additional router write-path wiring beyond the conditional poll
  endpoint already present.
- No push, no deploy.
