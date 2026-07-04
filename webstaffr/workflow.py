"""Workflow Definition — an ordered sequence of steps, scoped to one Tenant.

Every step input is treated as untrusted and validated before execution.
No secrets belong in a WorkflowDefinition.

Persistence note: a Step's `fn` is a Python callable and is never written to
storage -- serializing and later deserializing executable code from a
database is a real security hazard (arbitrary code execution from stored
data), not just an implementation inconvenience. Instead, only step *names*
are persisted, in order. StepRegistry maps a stable name back to a real
callable at load time, so a WorkflowDefinition rebuilt from storage is
exactly as safe as one built in code.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable

from .tenant import Tenant

StepFn = Callable[[dict], dict]


class InvalidWorkflowError(ValueError):
    """Raised when a workflow definition or one of its steps is malformed."""


class UnknownStepError(KeyError):
    """Raised when a persisted step name has no matching registered function."""


@dataclass(frozen=True)
class Step:
    """One step in a workflow: a name and the function it runs.

    The function receives the step's input dict and must return an output
    dict. It must not reach outside the process (no network, no disk, no
    external system) — this slice explicitly excludes external integrations.
    """

    name: str
    fn: StepFn

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise InvalidWorkflowError("Step name must be a non-empty string.")
        if not callable(self.fn):
            raise InvalidWorkflowError(f"Step {self.name!r} fn must be callable.")


@dataclass(frozen=True)
class WorkflowDefinition:
    """An ordered list of steps, scoped to exactly one Tenant."""

    workflow_id: str
    tenant: Tenant
    steps: tuple = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.workflow_id or not self.workflow_id.strip():
            raise InvalidWorkflowError("workflow_id must be a non-empty string.")
        if not isinstance(self.tenant, Tenant):
            raise InvalidWorkflowError("WorkflowDefinition.tenant must be a Tenant instance.")
        if not self.steps:
            raise InvalidWorkflowError(f"Workflow {self.workflow_id!r} must have at least one step.")
        names = [s.name for s in self.steps]
        if len(names) != len(set(names)):
            raise InvalidWorkflowError(f"Workflow {self.workflow_id!r} has duplicate step names: {names}")

    @property
    def step_names(self) -> list:
        """Ordered step names only -- the persistable shape of this workflow."""
        return [s.name for s in self.steps]

    @classmethod
    def from_step_names(
        cls,
        workflow_id: str,
        tenant: Tenant,
        step_names: Iterable[str],
        registry: "StepRegistry",
    ) -> "WorkflowDefinition":
        """Rebuild a WorkflowDefinition from persisted step names, resolving
        each name to a real callable via `registry`. Raises UnknownStepError
        for any name the registry doesn't recognize -- fails loudly rather
        than silently dropping a step."""
        steps = tuple(Step(name=name, fn=registry.get(name)) for name in step_names)
        return cls(workflow_id=workflow_id, tenant=tenant, steps=steps)


class StepRegistry:
    """Maps stable step names to callables, so persisted workflows can be
    rehydrated without ever deserializing code. Explicit and per-caller
    (not a hidden global) so tests and different call sites can have
    different registries without interfering with each other."""

    def __init__(self) -> None:
        self._fns: dict = {}

    def register(self, name: str, fn: StepFn) -> None:
        if not name or not name.strip():
            raise InvalidWorkflowError("Registered step name must be a non-empty string.")
        if not callable(fn):
            raise InvalidWorkflowError(f"Registered step {name!r} must be callable.")
        self._fns[name] = fn

    def get(self, name: str) -> StepFn:
        try:
            return self._fns[name]
        except KeyError:
            raise UnknownStepError(
                f"No step function registered for name {name!r}. "
                f"Known steps: {sorted(self._fns)}"
            ) from None

    def __contains__(self, name: str) -> bool:
        return name in self._fns
