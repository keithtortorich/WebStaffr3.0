"""Appointment booking -- tenant-scoped, persisted via SQLite (appointments
table, migration 0002). Separate from GHL sync: an appointment is recorded
locally first (source of truth for this system), then optionally synced
to GHL -- a GHL failure never prevents the local booking from succeeding.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from ...db import StorageError


@dataclass
class Appointment:
    tenant_id: str
    contact_name: str
    starts_at: str
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    notes: Optional[str] = None
    source: str = "angel"
    appointment_id: Optional[int] = None
    ghl_synced: bool = False


class AppointmentRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def save(self, appt: Appointment) -> int:
        try:
            self._conn.execute(
                "INSERT OR IGNORE INTO tenants (tenant_id) VALUES (?)", (appt.tenant_id,)
            )
            cursor = self._conn.execute(
                """
                INSERT INTO appointments
                    (tenant_id, contact_name, contact_phone, contact_email, starts_at,
                     notes, source, ghl_synced, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    appt.tenant_id,
                    appt.contact_name,
                    appt.contact_phone,
                    appt.contact_email,
                    appt.starts_at,
                    appt.notes,
                    appt.source,
                    int(appt.ghl_synced),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
        except sqlite3.Error as exc:
            raise StorageError(
                f"Failed to save appointment for tenant {appt.tenant_id!r}: {exc}"
            ) from exc
        appt.appointment_id = cursor.lastrowid
        return appt.appointment_id

    def mark_ghl_synced(self, tenant_id: str, appointment_id: int) -> None:
        try:
            self._conn.execute(
                "UPDATE appointments SET ghl_synced = 1 WHERE tenant_id = ? AND appointment_id = ?",
                (tenant_id, appointment_id),
            )
        except sqlite3.Error as exc:
            raise StorageError(f"Failed to mark appointment {appointment_id} synced: {exc}") from exc

    def list_for_tenant(self, tenant_id: str) -> list:
        try:
            rows = self._conn.execute(
                "SELECT appointment_id FROM appointments WHERE tenant_id = ? ORDER BY appointment_id",
                (tenant_id,),
            ).fetchall()
        except sqlite3.Error as exc:
            raise StorageError(f"Failed to list appointments for tenant {tenant_id!r}: {exc}") from exc
        return [row["appointment_id"] for row in rows]
