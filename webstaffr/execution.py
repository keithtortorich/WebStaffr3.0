"""Execution Record — the full, reconstructable trace of one workflow run.

An Execution Record must be sufficient to fully reconstruct what happened
in any given run. `to_dict`/`from_dict` here are the single source of truth
for that round trip -- the repository layer just moves the dict shape to
and from SQLite (as JSON) rather than knowing the record's internal
structure itself.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass
class StepTrace:
    """The record of one executed step: input, output, timestamp, status."""

    step_name: str
    status: ExecutionStatus
    input: dict
    output: Optional[dict] = None
    error: Optional[str] = None
    started_at: float = field(default_factory=time.time)
    finished_at: Optional[float] = None
    attempts: int = 0

    def to_dict(self) -> dict:
        return {
            "step_name": self.step_name,
            "status": self.status.value,
            "input": self.input,
            "output": self.output,
            "error": self.error,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "attempts": self.attempts,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "StepTrace":
        return cls(
            step_name=data["step_name"],
            status=ExecutionStatus(data["status"]),
            input=data["input"],
            output=data.get("output"),
            error=data.get("error"),
            started_at=data["started_at"],
            finished_at=data.get("finished_at"),
            attempts=data.get("attempts", 0),
        )


@dataclass
class ExecutionRecord:
    """Belongs to one Tenant; references one WorkflowDefinition; holds the
    full step-by-step trace of a single run."""

    tenant_id: str
    workflow_id: str
    status: ExecutionStatus = ExecutionStatus.PENDING
    steps: list = field(default_factory=list)
    started_at: float = field(default_factory=time.time)
    finished_at: Optional[float] = None
    execution_id: Optional[int] = None  # set once persisted; None for in-memory-only records

    def record_step(self, trace: StepTrace) -> None:
        self.steps.append(trace)

    def to_dict(self) -> dict:
        """Serialize for logging/inspection or persistence."""
        return {
            "execution_id": self.execution_id,
            "tenant_id": self.tenant_id,
            "workflow_id": self.workflow_id,
            "status": self.status.value,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "steps": [t.to_dict() for t in self.steps],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ExecutionRecord":
        record = cls(
            tenant_id=data["tenant_id"],
            workflow_id=data["workflow_id"],
            status=ExecutionStatus(data["status"]),
            started_at=data["started_at"],
            finished_at=data.get("finished_at"),
            execution_id=data.get("execution_id"),
        )
        record.steps = [StepTrace.from_dict(s) for s in data.get("steps", [])]
        return record
