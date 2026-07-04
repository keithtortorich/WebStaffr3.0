import os
import tempfile
import unittest

from fastapi.testclient import TestClient

from webstaffr.workers.angel.ghl import NullGHLClient
from webstaffr.workers.angel.router import create_app
from webstaffr.workers.angel.voice import NullVoiceBackend


class RouterTestCase(unittest.TestCase):
    """Uses a real temp-file SQLite DB rather than ':memory:' -- each
    sqlite3.connect(':memory:') call opens an independent, empty database,
    which would hide the startup migration from the router's per-request
    connections. A temp file behaves like the real deployment (one file,
    many connections)."""

    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.ghl = NullGHLClient()
        app = create_app(db_path=self.db_path, voice_backend=NullVoiceBackend(), ghl_client=self.ghl)
        # Enter the TestClient as a context manager so the app's ASGI
        # lifespan (startup -> migrate()) actually fires. TestClient(app)
        # without __enter__ does not reliably run lifespan events, which
        # is exactly the gap that let a "no such table" bug slip past
        # every endpoint that never happened to touch a table.
        self._client_ctx = TestClient(app)
        self.client = self._client_ctx.__enter__()

    def tearDown(self):
        self._client_ctx.__exit__(None, None, None)
        os.remove(self.db_path)


class TestHealthEndpoint(RouterTestCase):
    def test_health_ok(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"status": "ok"})


class TestChatEndpoint(RouterTestCase):
    def test_chat_returns_a_reply(self):
        resp = self.client.post("/chat", json={"tenant_id": "acme", "message": "Hi there"})
        self.assertEqual(resp.status_code, 200)
        self.assertIn("reply", resp.json())
        self.assertTrue(len(resp.json()["reply"]) > 0)

    def test_chat_rejects_invalid_tenant_id(self):
        resp = self.client.post("/chat", json={"tenant_id": "", "message": "Hi there"})
        self.assertEqual(resp.status_code, 400)


class TestBookEndpoint(RouterTestCase):
    def test_book_creates_appointment_without_ghl_sync(self):
        resp = self.client.post(
            "/book",
            json={
                "tenant_id": "acme",
                "contact_name": "Jane Doe",
                "starts_at": "2026-08-01T15:00:00Z",
                "contact_phone": "555-1234",
                "sync_to_ghl": False,
            },
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertIsInstance(body["appointment_id"], int)
        self.assertEqual(body["tenant_id"], "acme")
        self.assertEqual(body["contact_name"], "Jane Doe")
        self.assertFalse(body["ghl_synced"])

    def test_book_syncs_to_ghl_when_requested(self):
        resp = self.client.post(
            "/book",
            json={
                "tenant_id": "acme",
                "contact_name": "Jane Doe",
                "starts_at": "2026-08-01T15:00:00Z",
                "sync_to_ghl": True,
                "ghl_contact_id": "ghl_contact_123",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["ghl_synced"])
        self.assertEqual(len(self.ghl.created_appointments), 1)

    def test_book_rejects_invalid_tenant_id(self):
        resp = self.client.post(
            "/book",
            json={"tenant_id": "bad id with spaces", "contact_name": "Jane", "starts_at": "2026-08-01T15:00:00Z"},
        )
        self.assertEqual(resp.status_code, 400)

    def test_book_rejects_empty_contact_name(self):
        resp = self.client.post(
            "/book",
            json={"tenant_id": "acme", "contact_name": "   ", "starts_at": "2026-08-01T15:00:00Z"},
        )
        self.assertEqual(resp.status_code, 400)

    def test_book_rejects_empty_starts_at(self):
        resp = self.client.post(
            "/book",
            json={"tenant_id": "acme", "contact_name": "Jane", "starts_at": ""},
        )
        self.assertEqual(resp.status_code, 400)


class TestGHLWebhookEndpoint(RouterTestCase):
    def test_website_lead_event_is_handled(self):
        resp = self.client.post(
            "/webhooks/ghl",
            json={
                "tenant_id": "acme",
                "event_type": "website_lead",
                "contact_id": "c1",
                "contact_name": "Jane Doe",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "handled")

    def test_missed_call_event_is_handled(self):
        resp = self.client.post(
            "/webhooks/ghl",
            json={"tenant_id": "acme", "event_type": "missed_call", "contact_id": "c1"},
        )
        self.assertEqual(resp.status_code, 200)

    def test_unsupported_event_type_is_rejected(self):
        resp = self.client.post(
            "/webhooks/ghl",
            json={"tenant_id": "acme", "event_type": "not_a_real_event"},
        )
        self.assertEqual(resp.status_code, 400)

    def test_invalid_tenant_id_is_rejected(self):
        resp = self.client.post(
            "/webhooks/ghl",
            json={"tenant_id": "bad id with spaces", "event_type": "website_lead"},
        )
        self.assertEqual(resp.status_code, 400)


if __name__ == "__main__":
    unittest.main()
