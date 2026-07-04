import unittest

from webstaffr.execution import ExecutionStatus
from webstaffr.executor import StepInputError, TenantScopeViolation, WorkflowExecutor
from webstaffr.tenant import InvalidTenantError, Tenant
from webstaffr.workflow import InvalidWorkflowError, Step, WorkflowDefinition


def _add_one(data):
    return {"value": data["value"] + 1}


def _boom(data):
    raise RuntimeError("simulated step failure")


class TestTenant(unittest.TestCase):
    def test_valid_tenant(self):
        t = Tenant(tenant_id="acme")
        self.assertEqual(t.tenant_id, "acme")

    def test_invalid_tenant_id_rejected(self):
        with self.assertRaises(InvalidTenantError):
            Tenant(tenant_id="")
        with self.assertRaises(InvalidTenantError):
            Tenant(tenant_id="bad id with spaces")


class TestWorkflowDefinition(unittest.TestCase):
    def test_requires_at_least_one_step(self):
        tenant = Tenant(tenant_id="acme")
        with self.assertRaises(InvalidWorkflowError):
            WorkflowDefinition(workflow_id="wf1", tenant=tenant, steps=())

    def test_rejects_duplicate_step_names(self):
        tenant = Tenant(tenant_id="acme")
        with self.assertRaises(InvalidWorkflowError):
            WorkflowDefinition(
                workflow_id="wf1",
                tenant=tenant,
                steps=(Step("a", _add_one), Step("a", _add_one)),
            )

    def test_rejects_wrong_tenant_type(self):
        with self.assertRaises(InvalidWorkflowError):
            WorkflowDefinition(workflow_id="wf1", tenant="not-a-tenant", steps=(Step("a", _add_one),))


class TestWorkflowExecutor(unittest.TestCase):
    def setUp(self):
        self.tenant = Tenant(tenant_id="acme")
        self.executor = WorkflowExecutor()

    def test_successful_run_produces_full_trace(self):
        workflow = WorkflowDefinition(
            workflow_id="increment_twice",
            tenant=self.tenant,
            steps=(Step("inc1", _add_one), Step("inc2", _add_one)),
        )
        record = self.executor.run(self.tenant, workflow, {"value": 0})

        self.assertEqual(record.status, ExecutionStatus.SUCCEEDED)
        self.assertEqual(len(record.steps), 2)
        self.assertEqual(record.steps[-1].output, {"value": 2})
        self.assertIsNotNone(record.finished_at)

    def test_failed_step_halts_and_is_captured_in_record(self):
        workflow = WorkflowDefinition(
            workflow_id="will_fail",
            tenant=self.tenant,
            steps=(Step("ok", _add_one), Step("boom", _boom), Step("never_runs", _add_one)),
        )
        record = self.executor.run(self.tenant, workflow, {"value": 0})

        self.assertEqual(record.status, ExecutionStatus.FAILED)
        self.assertEqual(len(record.steps), 2)
        self.assertEqual(record.steps[-1].status, ExecutionStatus.FAILED)
        self.assertIn("simulated step failure", record.steps[-1].error)

    def test_tenant_scope_violation_raises(self):
        other_tenant = Tenant(tenant_id="other")
        workflow = WorkflowDefinition(
            workflow_id="wf1",
            tenant=self.tenant,
            steps=(Step("a", _add_one),),
        )
        with self.assertRaises(TenantScopeViolation):
            self.executor.run(other_tenant, workflow, {"value": 0})

    def test_untrusted_step_output_is_validated(self):
        def bad_step(data):
            return {"fn": lambda: None}

        workflow = WorkflowDefinition(
            workflow_id="wf1",
            tenant=self.tenant,
            steps=(Step("bad_output", bad_step),),
        )
        record = self.executor.run(self.tenant, workflow, {"value": 0})
        self.assertEqual(record.status, ExecutionStatus.FAILED)
        self.assertIn("must not be callable", record.steps[-1].error)

    def test_retry_recovers_from_transient_failure(self):
        attempts = {"count": 0}

        def flaky(data):
            attempts["count"] += 1
            if attempts["count"] < 2:
                raise RuntimeError("transient failure")
            return {"value": data["value"] + 1}

        workflow = WorkflowDefinition(
            workflow_id="flaky_wf",
            tenant=self.tenant,
            steps=(Step("flaky", flaky),),
        )
        executor = WorkflowExecutor(max_attempts_per_step=3)
        record = executor.run(self.tenant, workflow, {"value": 0})

        self.assertEqual(record.status, ExecutionStatus.SUCCEEDED)
        self.assertEqual(record.steps[0].attempts, 2)


if __name__ == "__main__":
    unittest.main()
