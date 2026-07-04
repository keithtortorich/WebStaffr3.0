"""Repository pattern for persisting WorkflowDefinitions and ExecutionRecords.

Every method takes tenant_id (or a tenant-scoped object) explicitly and
filters by it -- never a global, unscoped query. This mirrors the
tenant-isolation requirement at the persistence layer, not just in memory.

Repositories operate on an already-open sqlite3.Connection (see db.connect /
db.migrate) rather than owning connection lifecycle themselves, so callers
control transaction boundaries and tests can use a shared in-memory
connection.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Optional

from .db import StorageError
from .execution import ExecutionRecord
from .tenant import Tenant
from .workflow import StepRegistry, WorkflowDefinition


def _ensure_tenant(conn: sqlite3.Connection, tenant_id: str) -> None:
    """Upsert the tenant row so FK constraints on dependent tables are
    satisfied without callers having to manage tenant rows themselves."""
    conn.execute("INSERT OR IGNORE INTO tenants (tenant_id) VALUES (?)", (tenant_id,))


class WorkflowRepository:
    """Persists and loads WorkflowDefinitions. Step *behavior* (the `fn`
    callables) is never stored -- only step names, in order. Loading
    requires a StepRegistry to resolve names back to real functions."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def save(self, workflow: WorkflowDefinition) -> None:
        tenant_id = workflow.tenant.tenant_id
        try:
            _ensure_tenant(self._conn, tenant_id)
            self._conn.execute(
                """
                INSERT OR REPLACE INTO workflow_definitions
                    (tenant_id, workflow_id, step_names, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    tenant_id,
                    workflow.workflow_id,
                    json.dumps(workflow.step_names),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
        except sqlite3.Error as exc:
            raise StorageError(f"Failed to save workflow {workflow.workflow_id!r}: {exc}") from exc

    def load(self, tenant_id: str, workflow_id: str, registry: StepRegistry) -> Optional[WorkflowDefinition]:
        """Returns None if no such workflow exists for this tenant --
        tenant_id is always part of the lookup, so a workflow_id that
        exists under a *different* tenant is invisible here, not an error
        with information leakage."""
        try:
            row = self._conn.execute(
                """
                SELECT tenant_id, workflow_id, step_names
                FROM workflow_definitions
                WHERE tenant_id = ? AND workflow_id = ?
                """,
                (tenant_id, workflow_id),
            ).fetchone()
        except sqlite3.Error as exc:
            raise StorageError(f"Failed to load workflow {workflow_id!r}: {exc}") from exc

        if row is None:
            return None

        step_names = json.loads(row["step_names"])
        return WorkflowDefinition.from_step_names(
            workflow_id=row["workflow_id"],
            tenant=Tenant(tenant_id=row["tenant_id"]),
            step_names=step_names,
            registry=registry,
        )

    def list_for_tenant(self, tenant_id: str) -> list:
        try:
            rows = self._conn.execute(
                "SELECT workflow_id FROM workflow_definitions WHERE tenant_id = ? ORDER BY workflow_id",
                (tenant_id,),
            ).fetchall()
        except sqlite3.Error as exc:
            raise StorageError(f"Failed to list workflows for tenant {tenant_id!r}: {exc}") from exc
        return [row["workflow_id"] for row in rows]


class ExecutionRepository:
    """Persists and loads ExecutionRecords. Every execution is immutable,
    append-only history -- save() always inserts a new row, never updates
    an existing one."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def save(self, record: ExecutionRecord) -> int:
        """Returns the execution_id assigned to the newly persisted record."""
        try:
            _ensure_tenant(self._conn, record.tenant_id)
            cursor = self._conn.execute(
                """
                INSERT INTO execution_records
                    (tenant_id, workflow_id, status, started_at, finished_at, steps_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    record.tenant_id,
                    record.workflow_id,
                    record.status.value,
                    record.started_at,
                    record.finished_at,
                    json.dumps([s.to_dict() for s in record.steps]),
                ),
            )
        except sqlite3.Error as exc:
            raise StorageError(
                f"Failed to save execution record for workflow {record.workflow_id!r}: {exc}"
            ) from exc

        execution_id = cursor.lastrowid
        record.execution_id = execution_id
        return execution_id

    def load(self, tenant_id: str, execution_id: int) -> Optional[ExecutionRecord]:
        try:
            row = self._conn.execute(
                """
                SELECT execution_id, tenant_id, workflow_id, status, started_at, finished_at, steps_json
                FROM execution_records
                WHERE tenant_id = ? AND execution_id = ?
                """,
                (tenant_id, execution_id),
            ).fetchone()
        except sqlite3.Error as exc:
            raise StorageError(f"Failed to load execution record {execution_id}: {exc}") from exc

        if row is None:
            return None

        return ExecutionRecord.from_dict(
            {
                "execution_id": row["execution_id"],
                "tenant_id": row["tenant_id"],
                "workflow_id": row["workflow_id"],
                "status": row["status"],
                "started_at": row["started_at"],
                "finished_at": row["finished_at"],
                "steps": json.loads(row["steps_json"]),
            }
        )

    def list_for_tenant(self, tenant_id: str, workflow_id: Optional[str] = None) -> list:
        try:
            if workflow_id is not None:
                rows = self._conn.execute(
                    """
                    SELECT execution_id FROM execution_records
                    WHERE tenant_id = ? AND workflow_id = ?
                    ORDER BY execution_id
                    """,
                    (tenant_id, workflow_id),
                ).fetchall()
            else:
                rows = self._conn.execute(
                    "SELECT execution_id FROM execution_records WHERE tenant_id = ? ORDER BY execution_id",
                    (tenant_id,),
                ).fetchall()
        except sqlite3.Error as exc:
            raise StorageError(f"Failed to list executions for tenant {tenant_id!r}: {exc}") from exc
        return [row["execution_id"] for row in rows]
