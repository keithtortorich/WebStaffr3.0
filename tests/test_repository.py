import unittest

from webstaffr.db import StorageError, connect, migrate
from webstaffr.execution import ExecutionStatus
from webstaffr.executor import WorkflowExecutor
from webstaffr.repository import ExecutionRepository, WorkflowRepository
from webstaffr.tenant import Tenant
from webstaffr.workflow import StepRegistry, UnknownStepError, WorkflowDefinition, Step


def _double(data):
    return {"value": data["value"] * 2}


def _add_ten(data):
    return {"value": data["value"] + 10}


class RepositoryTestCase(unittest.TestCase):
    """Each test gets its own fresh in-memory database and migrates it,
    matching how a real caller would bootstrap a connection."""

    def setUp(self):
        self._ctx = connect(":memory:")
        self.conn = self._ctx.__enter__()
        migrate(self.conn)
        self.registry = StepRegistry()
        self.registry.register("double", _double)
        self.registry.register("add_ten", _add_ten)

    def tearDown(self):
        self._ctx.__exit__(None, None, None)


class TestMigrate(RepositoryTestCase):
    def test_migrate_is_idempotent(self):
        # setUp already migrated once; calling again must be a no-op, not an error.
        applied_again = migrate(self.conn)
        self.assertEqual(applied_again, [])

    def test_expected_tables_exist(self):
        tables = {
            row["name"]
            for row in self.conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        self.assertTrue({"tenants", "workflow_definitions", "execution_records", "schema_migrations"} <= tables)


class TestWorkflowRepository(RepositoryTestCase):
    def test_save_and_load_round_trip(self):
        tenant = Tenant(tenant_id="acme")
        workflow = WorkflowDefinition(
            workflow_id="double_then_add",
            tenant=tenant,
            steps=(Step("double", _double), Step("add_ten", _add_ten)),
        )
        repo = WorkflowRepository(self.conn)
        repo.save(workflow)

        loaded = repo.load("acme", "double_then_add", self.registry)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.workflow_id, "double_then_add")
        self.assertEqual(loaded.tenant.tenant_id, "acme")
        self.assertEqual(loaded.step_names, ["double", "add_ten"])

        # And the rebuilt workflow must actually run correctly.
        record = WorkflowExecutor().run(tenant, loaded, {"value": 3})
        self.assertEqual(record.status, ExecutionStatus.SUCCEEDED)
        self.assertEqual(record.steps[-1].output, {"value": 16})  # (3*2)+10

    def test_load_missing_workflow_returns_none(self):
        repo = WorkflowRepository(self.conn)
        self.assertIsNone(repo.load("acme", "does_not_exist", self.registry))

    def test_load_is_tenant_scoped(self):
        tenant_a = Tenant(tenant_id="tenant_a")
        workflow = WorkflowDefinition(
            workflow_id="shared_name",
            tenant=tenant_a,
            steps=(Step("double", _double),),
        )
        repo = WorkflowRepository(self.conn)
        repo.save(workflow)

        # Same workflow_id, different tenant -- must not be visible.
        self.assertIsNone(repo.load("tenant_b", "shared_name", self.registry))
        self.assertIsNotNone(repo.load("tenant_a", "shared_name", self.registry))

    def test_load_with_unknown_step_name_raises(self):
        tenant = Tenant(tenant_id="acme")
        workflow = WorkflowDefinition(
            workflow_id="wf1",
            tenant=tenant,
            steps=(Step("double", _double),),
        )
        repo = WorkflowRepository(self.conn)
        repo.save(workflow)

        empty_registry = StepRegistry()
        with self.assertRaises(UnknownStepError):
            repo.load("acme", "wf1", empty_registry)

    def test_list_for_tenant(self):
        tenant = Tenant(tenant_id="acme")
        repo = WorkflowRepository(self.conn)
        repo.save(WorkflowDefinition(workflow_id="wf_a", tenant=tenant, steps=(Step("double", _double),)))
        repo.save(WorkflowDefinition(workflow_id="wf_b", tenant=tenant, steps=(Step("double", _double),)))
        self.assertEqual(repo.list_for_tenant("acme"), ["wf_a", "wf_b"])
        self.assertEqual(repo.list_for_tenant("other_tenant"), [])


class TestExecutionRepository(RepositoryTestCase):
    def test_save_and_load_round_trip(self):
        tenant = Tenant(tenant_id="acme")
        workflow = WorkflowDefinition(
            workflow_id="wf1",
            tenant=tenant,
            steps=(Step("double", _double), Step("add_ten", _add_ten)),
        )
        WorkflowRepository(self.conn).save(workflow)  # FK requires the workflow to exist first

        record = WorkflowExecutor().run(tenant, workflow, {"value": 5})
        exec_repo = ExecutionRepository(self.conn)
        execution_id = exec_repo.save(record)
        self.assertIsInstance(execution_id, int)

        loaded = exec_repo.load("acme", execution_id)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.status, ExecutionStatus.SUCCEEDED)
        self.assertEqual(len(loaded.steps), 2)
        self.assertEqual(loaded.steps[-1].output, {"value": 20})

    def test_load_is_tenant_scoped(self):
        tenant = Tenant(tenant_id="acme")
        workflow = WorkflowDefinition(workflow_id="wf1", tenant=tenant, steps=(Step("double", _double),))
        WorkflowRepository(self.conn).save(workflow)
        record = WorkflowExecutor().run(tenant, workflow, {"value": 1})
        execution_id = ExecutionRepository(self.conn).save(record)

        self.assertIsNone(ExecutionRepository(self.conn).load("someone_else", execution_id))

    def test_failed_execution_is_persisted_faithfully(self):
        def boom(_data):
            raise RuntimeError("simulated failure")

        tenant = Tenant(tenant_id="acme")
        workflow = WorkflowDefinition(workflow_id="wf_fail", tenant=tenant, steps=(Step("boom", boom),))
        WorkflowRepository(self.conn).save(workflow)

        record = WorkflowExecutor().run(tenant, workflow, {})
        execution_id = ExecutionRepository(self.conn).save(record)

        loaded = ExecutionRepository(self.conn).load("acme", execution_id)
        self.assertEqual(loaded.status, ExecutionStatus.FAILED)
        self.assertIn("simulated failure", loaded.steps[-1].error)

    def test_list_for_tenant_and_workflow(self):
        tenant = Tenant(tenant_id="acme")
        workflow = WorkflowDefinition(workflow_id="wf1", tenant=tenant, steps=(Step("double", _double),))
        WorkflowRepository(self.conn).save(workflow)
        exec_repo = ExecutionRepository(self.conn)
        id1 = exec_repo.save(WorkflowExecutor().run(tenant, workflow, {"value": 1}))
        id2 = exec_repo.save(WorkflowExecutor().run(tenant, workflow, {"value": 2}))

        self.assertEqual(exec_repo.list_for_tenant("acme"), [id1, id2])
        self.assertEqual(exec_repo.list_for_tenant("acme", workflow_id="wf1"), [id1, id2])
        self.assertEqual(exec_repo.list_for_tenant("acme", workflow_id="no_such_workflow"), [])


if __name__ == "__main__":
    unittest.main()
