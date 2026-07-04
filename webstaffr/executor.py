"""Workflow Executor — runs one WorkflowDefinition instance, step by step,
to completion, producing an ExecutionRecord.

Execution model: sequential, single-instance, run-to-completion. No
concurrency, scheduling, or multi-instance coordination in this slice.

Resilience note: per-step retry is a bounded, single-step behavior (a step
may retry itself a fixed number of times on failure) and is NOT the same as
re-scheduling or re-coordinating whole workflow *instances*, which this
slice still does not do. Kept conservative and off by default
(max_attempts_per_step=1) so no hidden complexity is introduced beyond what
was asked for.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Optional

from .execution import ExecutionRecord, ExecutionStatus, StepTrace
from .tenant import Tenant
from .workflow import Step, WorkflowDefinition

logger = logging.getLogger("webstaffr.executor")


class TenantScopeViolation(RuntimeError):
    """Raised when a workflow's tenant does not match the execution's tenant."""


class StepInputError(ValueError):
    """Raised when a step's input or output fails validation."""


def _validate_step_payload(step_name: str, data: Any, *, label: str) -> dict:
    """Every step input/output is treated as untrusted. Must be a plain
    dict with string keys and no callables — no hidden state, nothing that
    could carry a secret or behavior by accident of type."""
    if not isinstance(data, dict):
        raise StepInputError(
            f"Step {step_name!r} {label} must be a dict, got {type(data).__name__}."
        )
    for key, value in data.items():
        if not isinstance(key, str):
            raise StepInputError(f"Step {step_name!r} {label} has non-string key: {key!r}")
        if callable(value):
            raise StepInputError(
                f"Step {step_name!r} {label} value for {key!r} must not be callable."
            )
    return data


class WorkflowExecutor:
    """Runs exactly one WorkflowDefinition instance for exactly one Tenant."""

    def __init__(self, max_attempts_per_step: int = 1) -> None:
        if max_attempts_per_step < 1:
            raise ValueError("max_attempts_per_step must be >= 1.")
        self.max_attempts_per_step = max_attempts_per_step

    def run(
        self,
        tenant: Tenant,
        workflow: WorkflowDefinition,
        initial_input: Optional[dict] = None,
    ) -> ExecutionRecord:
        """Execute every step of `workflow` in order for `tenant`.

        Returns an ExecutionRecord regardless of success or failure — the
        record itself is the source of truth for what happened; callers
        should never need to catch an exception to learn the outcome of a
        step failure. This method raises only for programmer-error-shaped
        problems (tenant scope mismatch) that indicate misuse, not for
        step-execution failures, which are captured in the record instead.
        """
        if workflow.tenant.tenant_id != tenant.tenant_id:
            raise TenantScopeViolation(
                f"Workflow {workflow.workflow_id!r} belongs to tenant "
                f"{workflow.tenant.tenant_id!r}, not {tenant.tenant_id!r}."
            )

        record = ExecutionRecord(
            tenant_id=tenant.tenant_id,
            workflow_id=workflow.workflow_id,
            status=ExecutionStatus.RUNNING,
        )
        logger.info(
            "workflow_run_started tenant=%s workflow=%s",
            tenant.tenant_id,
            workflow.workflow_id,
        )

        current_input: dict = dict(initial_input or {})

        for step in workflow.steps:
            trace = self._run_step(step, current_input)
            record.record_step(trace)

            if trace.status == ExecutionStatus.FAILED:
                record.status = ExecutionStatus.FAILED
                record.finished_at = time.time()
                logger.error(
                    "workflow_run_failed tenant=%s workflow=%s step=%s error=%s",
                    tenant.tenant_id,
                    workflow.workflow_id,
                    step.name,
                    trace.error,
                )
                return record

            # Explicit data flow: this step's output becomes the next
            # step's input. No implicit shared state between steps.
            current_input = trace.output or {}

        record.status = ExecutionStatus.SUCCEEDED
        record.finished_at = time.time()
        logger.info(
            "workflow_run_succeeded tenant=%s workflow=%s",
            tenant.tenant_id,
            workflow.workflow_id,
        )
        return record

    def _run_step(self, step: Step, data: dict) -> StepTrace:
        trace = StepTrace(
            step_name=step.name,
            status=ExecutionStatus.RUNNING,
            input=dict(data),
        )

        last_exc: Optional[Exception] = None
        for attempt in range(1, self.max_attempts_per_step + 1):
            trace.attempts = attempt
            try:
                validated_input = _validate_step_payload(step.name, data, label="input")
                output = step.fn(validated_input)
                validated_output = _validate_step_payload(step.name, output, label="output")
                trace.output = validated_output
                trace.status = ExecutionStatus.SUCCEEDED
                trace.finished_at = time.time()
                return trace
            except Exception as exc:  # noqa: BLE001 — deliberately broad: any
                # step failure must degrade gracefully into the record,
                # never crash the executor or take down unrelated runs.
                last_exc = exc
                logger.warning(
                    "step_attempt_failed step=%s attempt=%d/%d error=%s",
                    step.name,
                    attempt,
                    self.max_attempts_per_step,
                    exc,
                )

        trace.status = ExecutionStatus.FAILED
        trace.error = f"{type(last_exc).__name__}: {last_exc}" if last_exc else "Unknown failure."
        trace.finished_at = time.time()
        return trace
