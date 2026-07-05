import os
import sqlite3
import tempfile
import unittest

from fastapi.testclient import TestClient

from webstaffr.workers.angel.router import create_app


def _valid_payload(**overrides):
    payload = {
        "biz_name": "Desert Pro Plumbing",
        "phone": "602-555-0100",
        "email": "owner@example.com",
        "industry": "Plumber",
        "service_area": "Phoenix, AZ",
        "tagline": "Fast, honest plumbing.",
        "differentiator": "We show up on time, every time.",
        "services": ["Leak Repair", "Drain Cleaning"],
        "license_number": "ROC 999999",
        "plan": "growth",
        "lead_routing": "Text Maria at 602-555-0101, replies within 1 hour.",
        "approver": "Maria Lopez",
    }
    payload.update(overrides)
    return payload


class IntakeTestCase(unittest.TestCase):
    """Same temp-file-db + lifespan-context pattern as RouterTestCase in
    test_router.py -- see that file for why ':memory:' doesn't work here."""

    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        app = create_app(db_path=self.db_path)
        self._client_ctx = TestClient(app)
        self.client = self._client_ctx.__enter__()

    def tearDown(self):
        self._client_ctx.__exit__(None, None, None)
        os.remove(self.db_path)


class TestIntakeSubmission(IntakeTestCase):
    def test_valid_submission_returns_generated_tenant_id(self):
        resp = self.client.post("/intake", json=_valid_payload())
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertIsInstance(body["submission_id"], int)
        self.assertTrue(body["tenant_id"].startswith("desert_pro_plumbing_"))
        self.assertEqual(body["biz_name"], "Desert Pro Plumbing")
        self.assertEqual(body["industry"], "Plumber")
        self.assertEqual(body["plan"], "growth")

    def test_submission_creates_tenant_row(self):
        resp = self.client.post("/intake", json=_valid_payload())
        tenant_id = resp.json()["tenant_id"]

        conn = sqlite3.connect(self.db_path)
        try:
            row = conn.execute(
                "SELECT tenant_id FROM tenants WHERE tenant_id = ?", (tenant_id,)
            ).fetchone()
        finally:
            conn.close()
        self.assertIsNotNone(row)

    def test_submission_persists_full_row(self):
        resp = self.client.post("/intake", json=_valid_payload(rating_value=4.8, review_count=214))
        tenant_id = resp.json()["tenant_id"]
        submission_id = resp.json()["submission_id"]

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            row = conn.execute(
                "SELECT * FROM intake_submissions WHERE tenant_id = ? AND submission_id = ?",
                (tenant_id, submission_id),
            ).fetchone()
        finally:
            conn.close()
        self.assertIsNotNone(row)
        self.assertEqual(row["biz_name"], "Desert Pro Plumbing")
        self.assertEqual(row["rating_value"], 4.8)
        self.assertEqual(row["review_count"], 214)
        self.assertIn("Leak Repair", row["services_json"])

    def test_two_businesses_with_same_name_get_different_tenant_ids(self):
        r1 = self.client.post("/intake", json=_valid_payload())
        r2 = self.client.post("/intake", json=_valid_payload())
        self.assertNotEqual(r1.json()["tenant_id"], r2.json()["tenant_id"])


class TestIntakeValidation(IntakeTestCase):
    def test_missing_required_field_is_rejected(self):
        resp = self.client.post("/intake", json={"biz_name": "Test"})
        self.assertEqual(resp.status_code, 422)

    def test_empty_services_list_is_rejected(self):
        resp = self.client.post("/intake", json=_valid_payload(services=[]))
        self.assertEqual(resp.status_code, 400)

    def test_invalid_plan_is_rejected(self):
        resp = self.client.post("/intake", json=_valid_payload(plan="enterprise"))
        self.assertEqual(resp.status_code, 400)

    def test_rating_value_out_of_range_is_rejected(self):
        resp = self.client.post("/intake", json=_valid_payload(rating_value=9.0))
        self.assertEqual(resp.status_code, 400)

    def test_no_submission_is_persisted_on_validation_failure(self):
        self.client.post("/intake", json=_valid_payload(plan="enterprise"))
        conn = sqlite3.connect(self.db_path)
        try:
            count = conn.execute("SELECT COUNT(*) FROM intake_submissions").fetchone()[0]
        finally:
            conn.close()
        self.assertEqual(count, 0)


class TestTradePresets(IntakeTestCase):
    def test_list_presets_returns_all_industries(self):
        resp = self.client.get("/intake/presets")
        self.assertEqual(resp.status_code, 200)
        industries = resp.json()["industries"]
        self.assertIn("HVAC", industries)
        self.assertIn("Plumber", industries)
        self.assertIn("Other", industries)

    def test_known_industry_returns_matching_preset(self):
        resp = self.client.get("/intake/presets/HVAC")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["industry"], "HVAC")
        self.assertIn("tagline", body["hints"])
        self.assertIn("options", body["software"])

    def test_industry_alias_resolves_to_canonical_preset(self):
        resp = self.client.get("/intake/presets/Plumbing")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["industry"], "Plumber")

    def test_unknown_industry_falls_back_to_other(self):
        resp = self.client.get("/intake/presets/Astrology")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["industry"], "Other")


class TestIntakeCORSScoping(IntakeTestCase):
    """/intake and /intake/presets are browser-facing (the intake form runs
    on an arbitrary origin, same as the /chat widget) so they need CORS --
    unlike /book and /webhooks/ghl, see test_router.py's TestCORSScoping."""

    def test_intake_has_cors_header_for_arbitrary_origin(self):
        resp = self.client.post(
            "/intake",
            json=_valid_payload(),
            headers={"Origin": "https://some-marketing-site.example.com"},
        )
        self.assertEqual(resp.headers.get("access-control-allow-origin"), "*")

    def test_intake_presets_has_cors_header(self):
        resp = self.client.get(
            "/intake/presets/HVAC",
            headers={"Origin": "https://some-marketing-site.example.com"},
        )
        self.assertEqual(resp.headers.get("access-control-allow-origin"), "*")


if __name__ == "__main__":
    unittest.main()
