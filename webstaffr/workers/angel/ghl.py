"""GoHighLevel (GHL) integration for Angel: syncing notes and appointments.

Same pattern as voice.py -- an explicit interface, a safe Null default, and
a real client that requires credentials and fails loudly without them.
Uses stdlib urllib only, to avoid adding `requests` as another dependency
for what is currently a small, infrequent call surface.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Optional, Protocol


class GHLNotConfiguredError(RuntimeError):
    """Raised when the GHL client is used without required credentials."""


class GHLSyncError(RuntimeError):
    """Raised when a GHL API call fails."""


class GHLClient(Protocol):
    def log_note(self, contact_id: str, note: str) -> None: ...
    def create_appointment(self, contact_id: str, starts_at: str, notes: str) -> dict: ...
    def update_appointment(self, appointment_id: str, starts_at: str, notes: str) -> dict: ...
    def cancel_appointment(self, appointment_id: str) -> dict: ...


class NullGHLClient:
    """Safe default: records calls in memory, makes no network requests.
    Used for tests and for any tenant that hasn't configured GHL yet."""

    def __init__(self) -> None:
        self.logged_notes: list = []
        self.created_appointments: list = []
        self.updated_appointments: list = []
        self.cancelled_appointments: list = []

    def log_note(self, contact_id: str, note: str) -> None:
        self.logged_notes.append({"contact_id": contact_id, "note": note})

    def create_appointment(self, contact_id: str, starts_at: str, notes: str) -> dict:
        record = {"contact_id": contact_id, "starts_at": starts_at, "notes": notes, "ghl_id": None}
        self.created_appointments.append(record)
        return record

    def update_appointment(self, appointment_id: str, starts_at: str, notes: str) -> dict:
        record = {
            "appointment_id": appointment_id,
            "starts_at": starts_at,
            "notes": notes,
            "action": "updated",
        }
        self.updated_appointments.append(record)
        return record

    def cancel_appointment(self, appointment_id: str) -> dict:
        record = {"appointment_id": appointment_id, "action": "cancelled"}
        self.cancelled_appointments.append(record)
        return record


class GoHighLevelClient:
    """Real GHL client. Requires GHL_API_KEY and GHL_LOCATION_ID. Fails
    loudly at construction if not configured -- never silently degrades
    to a no-op that looks like success."""

    BASE_URL = "https://services.leadconnectorhq.com"

    def __init__(self, api_key: Optional[str] = None, location_id: Optional[str] = None) -> None:
        self.api_key = api_key or os.environ.get("GHL_API_KEY")
        self.location_id = location_id or os.environ.get("GHL_LOCATION_ID")
        if not self.api_key or not self.location_id:
            raise GHLNotConfiguredError(
                "GoHighLevelClient requires GHL_API_KEY and GHL_LOCATION_ID "
                "(env vars or constructor args). Refusing to start with no credentials."
            )

    def _request(self, method: str, path: str, payload: Optional[dict] = None) -> dict:
        url = f"{self.BASE_URL}{path}"
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        req = urllib.request.Request(
            url,
            data=data,
            method=method,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Version": "2021-07-28",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                body = resp.read().decode("utf-8")
                return json.loads(body) if body else {}
        except urllib.error.HTTPError as exc:
            raise GHLSyncError(f"GHL API error {exc.code} on {method} {path}: {exc.read()}") from exc
        except urllib.error.URLError as exc:
            raise GHLSyncError(f"GHL API unreachable for {method} {path}: {exc}") from exc

    def log_note(self, contact_id: str, note: str) -> None:
        self._request("POST", f"/contacts/{contact_id}/notes", {"body": note})

    def create_appointment(self, contact_id: str, starts_at: str, notes: str) -> dict:
        return self._request(
            "POST",
            "/calendars/events/appointments",
            {
                "locationId": self.location_id,
                "contactId": contact_id,
                "startTime": starts_at,
                "notes": notes,
            },
        )

    def update_appointment(self, appointment_id: str, starts_at: str, notes: str) -> dict:
        # [Unverified] endpoint/payload shape -- no live GHL account to
        # confirm against; same treatment as the model name in voice.py.
        return self._request(
            "PUT",
            f"/calendars/events/appointments/{appointment_id}",
            {
                "startTime": starts_at,
                "notes": notes,
            },
        )

    def cancel_appointment(self, appointment_id: str) -> dict:
        # [Unverified] endpoint -- no live GHL account to confirm against.
        return self._request("DELETE", f"/calendars/events/appointments/{appointment_id}")
