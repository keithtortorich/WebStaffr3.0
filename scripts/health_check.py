#!/usr/bin/env python3
"""Self-healing health check for the WebStaffr in-memory + SQLite slice.

Run any time to verify the core components import cleanly, a minimal
smoke-test workflow still executes correctly end to end, and the SQLite
persistence layer can migrate, save, and load correctly. Exits non-zero on
any failure so it can be wired into CI later without modification.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main() -> int:
    checks = []

    def check(name, fn):
        try:
            fn()
            checks.append((name, True, ""))
        except Exception as exc:  # noqa: BLE001
            checks.append((name, False, f"{type(exc).__name__}: {exc}"))

    def check_imports():
        from webstaffr.tenant import Tenant  # noqa: F401
        from webstaffr.workflow import Step, WorkflowDefinition, StepRegistry  # noqa: F401
        from webstaffr.execution import ExecutionRecord, ExecutionStatus  # noqa: F401
        from webstaffr.executor import WorkflowExecutor  # noqa: F401
        from webstaffr.db import connect, migrate  # noqa: F401
        from webstaffr.repository import WorkflowRepository, ExecutionRepository  # noqa: F401

    def check_smoke_workflow():
        from webstaffr.tenant import Tenant
        from webstaffr.workflow import Step, WorkflowDefinition
        from webstaffr.execution import ExecutionStatus
        from webstaffr.executor import WorkflowExecutor

        tenant = Tenant(tenant_id="healthcheck")
        workflow = WorkflowDefinition(
            workflow_id="smoke_test",
            tenant=tenant,
            steps=(
                Step("double", lambda d: {"value": d["value"] * 2}),
                Step("add_ten", lambda d: {"value": d["value"] + 10}),
            ),
        )
        record = WorkflowExecutor().run(tenant, workflow, {"value": 5})
        assert record.status == ExecutionStatus.SUCCEEDED, f"unexpected status: {record.status}"
        assert record.steps[-1].output == {"value": 20}, f"unexpected output: {record.steps[-1].output}"

    def check_tenant_isolation_enforced():
        from webstaffr.tenant import Tenant
        from webstaffr.workflow import Step, WorkflowDefinition
        from webstaffr.executor import WorkflowExecutor, TenantScopeViolation

        tenant_a = Tenant(tenant_id="tenant_a")
        tenant_b = Tenant(tenant_id="tenant_b")
        workflow = WorkflowDefinition(
            workflow_id="wf",
            tenant=tenant_a,
            steps=(Step("noop", lambda d: d),),
        )
        try:
            WorkflowExecutor().run(tenant_b, workflow, {})
            raise AssertionError("expected TenantScopeViolation, none raised")
        except TenantScopeViolation:
            pass

    def check_failed_step_does_not_crash_executor():
        from webstaffr.tenant import Tenant
        from webstaffr.workflow import Step, WorkflowDefinition
        from webstaffr.execution import ExecutionStatus
        from webstaffr.executor import WorkflowExecutor

        def boom(_d):
            raise RuntimeError("intentional failure for health check")

        tenant = Tenant(tenant_id="healthcheck")
        workflow = WorkflowDefinition(
            workflow_id="failure_smoke_test",
            tenant=tenant,
            steps=(Step("boom", boom),),
        )
        record = WorkflowExecutor().run(tenant, workflow, {})
        assert record.status == ExecutionStatus.FAILED
        assert "intentional failure" in record.steps[-1].error

    def check_sqlite_persistence_round_trip():
        from webstaffr.tenant import Tenant
        from webstaffr.workflow import Step, StepRegistry, WorkflowDefinition
        from webstaffr.execution import ExecutionStatus
        from webstaffr.executor import WorkflowExecutor
        from webstaffr.db import connect, migrate
        from webstaffr.repository import ExecutionRepository, WorkflowRepository

        with connect(":memory:") as conn:
            applied = migrate(conn)
            assert isinstance(applied, list)

            tenant = Tenant(tenant_id="healthcheck")
            registry = StepRegistry()
            registry.register("double", lambda d: {"value": d["value"] * 2})

            workflow = WorkflowDefinition(
                workflow_id="persist_smoke_test",
                tenant=tenant,
                steps=(Step("double", registry.get("double")),),
            )
            WorkflowRepository(conn).save(workflow)
            loaded_workflow = WorkflowRepository(conn).load(
                "healthcheck", "persist_smoke_test", registry
            )
            assert loaded_workflow is not None, "workflow failed to round-trip"

            record = WorkflowExecutor().run(tenant, loaded_workflow, {"value": 4})
            assert record.status == ExecutionStatus.SUCCEEDED

            execution_id = ExecutionRepository(conn).save(record)
            loaded_record = ExecutionRepository(conn).load("healthcheck", execution_id)
            assert loaded_record is not None, "execution record failed to round-trip"
            assert loaded_record.steps[-1].output == {"value": 8}

            # Tenant isolation must hold at the storage layer too.
            assert WorkflowRepository(conn).load("someone_else", "persist_smoke_test", registry) is None

    def check_angel_imports():
        from webstaffr.workers.angel.angel import Angel, load_prompt_template  # noqa: F401
        from webstaffr.workers.angel.voice import NullVoiceBackend  # noqa: F401
        from webstaffr.workers.angel.ghl import NullGHLClient  # noqa: F401
        from webstaffr.workers.angel.router import create_app  # noqa: F401

    def check_angel_booking_round_trip():
        from webstaffr.tenant import Tenant
        from webstaffr.db import connect, migrate
        from webstaffr.workers.angel.angel import Angel
        from webstaffr.workers.angel.ghl import NullGHLClient
        from webstaffr.workers.angel.booking import AppointmentRepository

        with connect(":memory:") as conn:
            migrate(conn)
            tenant = Tenant(tenant_id="healthcheck")
            ghl = NullGHLClient()
            angel = Angel(tenant=tenant, conn=conn, ghl_client=ghl)

            appt = angel.book_appointment(
                contact_name="Health Check",
                starts_at="2026-08-01T00:00:00Z",
                sync_to_ghl=True,
                ghl_contact_id="hc_contact",
            )
            assert appt.appointment_id is not None
            assert appt.ghl_synced is True, "expected GHL sync to succeed against NullGHLClient"

            stored = AppointmentRepository(conn).list_for_tenant("healthcheck")
            assert stored == [appt.appointment_id]

    def check_angel_router_smoke():
        # FastAPI's TestClient -- no real network socket, no external process.
        # Uses a real temp file, not ":memory:" -- each sqlite3.connect(":memory:")
        # call opens an independent empty DB, which would hide the startup
        # migration from the router's per-request connections.
        import os
        import tempfile

        from fastapi.testclient import TestClient
        from webstaffr.workers.angel.router import create_app
        from webstaffr.workers.angel.voice import NullVoiceBackend
        from webstaffr.workers.angel.ghl import NullGHLClient

        fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        try:
            app = create_app(db_path=db_path, voice_backend=NullVoiceBackend(), ghl_client=NullGHLClient())
            # Must enter as a context manager for the app's lifespan
            # (startup -> migrate()) to actually fire -- see router.py's
            # create_app() docstring for why migration isn't run eagerly
            # inside the factory itself.
            with TestClient(app) as client:
                _run_angel_router_smoke_requests(client)
        finally:
            os.remove(db_path)

    def _run_angel_router_smoke_requests(client):

        health_resp = client.get("/health")
        assert health_resp.status_code == 200, f"unexpected /health status: {health_resp.status_code}"

        chat_resp = client.post("/chat", json={"tenant_id": "healthcheck", "message": "hi"})
        assert chat_resp.status_code == 200, f"unexpected /chat status: {chat_resp.status_code}"
        assert "reply" in chat_resp.json()

        webhook_resp = client.post(
            "/webhooks/ghl",
            json={"tenant_id": "healthcheck", "event_type": "website_lead", "contact_name": "Jane"},
        )
        assert webhook_resp.status_code == 200, f"unexpected /webhooks/ghl status: {webhook_resp.status_code}"

        book_resp = client.post(
            "/book",
            json={
                "tenant_id": "healthcheck",
                "contact_name": "Jane",
                "starts_at": "2026-08-01T15:00:00Z",
                "sync_to_ghl": False,
            },
        )
        assert book_resp.status_code == 200, f"unexpected /book status: {book_resp.status_code}"
        assert book_resp.json()["appointment_id"] is not None

    check("imports", check_imports)
    check("smoke_workflow_executes_and_succeeds", check_smoke_workflow)
    check("tenant_isolation_enforced", check_tenant_isolation_enforced)
    check("failed_step_degrades_gracefully", check_failed_step_does_not_crash_executor)
    check("sqlite_persistence_round_trip", check_sqlite_persistence_round_trip)
    check("angel_imports", check_angel_imports)
    check("angel_booking_round_trip", check_angel_booking_round_trip)
    check("angel_router_smoke", check_angel_router_smoke)

    print("WebStaffr health check")
    print("=" * 40)
    all_ok = True
    for name, ok, error in checks:
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {name}" + (f" -- {error}" if error else ""))
        all_ok = all_ok and ok

    print("=" * 40)
    print("Result: " + ("HEALTHY" if all_ok else "UNHEALTHY"))
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
