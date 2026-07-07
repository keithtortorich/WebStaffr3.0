"""End-to-end smoke test for the real intake -> generated customer site ->
Angel widget pipeline in THIS repo (webstaffr/), driven in-process via
FastAPI's TestClient against a temp SQLite DB. No credentials needed --
Angel defaults to NullVoiceBackend/NullGHLClient when none are configured.

This is deliberately not a rubber stamp: every stage checks actual content
(DB row values, response body fields, widget request-shape match) rather
than just "did we get a 200" or "does a file exist" -- status codes and
file presence are exactly the kind of check that would have missed the
bugs this script already found.

Usage:
    python3 scripts/onboarding_smoketest.py
"""
import json
import os
import sqlite3
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient  # noqa: E402

from webstaffr.workers.angel.router import create_app  # noqa: E402
from webstaffr.intake import IntakeRepository  # noqa: E402

FAILURES = []


def check(label, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}" + (f" -- {detail}" if detail and not condition else ""))
    if not condition:
        FAILURES.append(label)


def main():
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        app = create_app(db_path=db_path)  # no voice_backend/ghl_client -> Null defaults
        with TestClient(app) as client:
            # Stage 0: app boots and serves /health
            resp = client.get("/health")
            check("0. app boots, /health returns 200", resp.status_code == 200, resp.text)

            # Stage 1: submit a realistic intake payload, including a mix of
            # set and deliberately-omitted optional fields.
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
                # internal-only fields that must NEVER reach the public site:
                "competitors": "Valley Plumbing Co, worried they undercut us on price",
                "timeline": "internal target: launch by Aug 1",
                "notes": "founder is picky about the logo color",
                # a real rating, to check it DOES appear publicly:
                "rating_value": 4.9,
                "review_count": 214,
            }
            submit = client.post("/intake", json=payload)
            check("1. POST /intake returns 200", submit.status_code == 200, submit.text)
            body = submit.json()
            tenant_id = body.get("tenant_id")
            check("1b. response includes a tenant_id", bool(tenant_id), body)

            # Stage 2: verify the ACTUAL DB row, not just the HTTP response
            # -- the API could claim success without truly persisting.
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            try:
                repo = IntakeRepository(conn)
                saved = repo.load_latest_for_tenant(tenant_id)
            finally:
                conn.close()
            check("2. intake row actually persisted", saved is not None)
            if saved:
                check(
                    "2b. persisted row matches submitted data",
                    saved.biz_name == payload["biz_name"] and saved.competitors == payload["competitors"],
                    f"biz_name={saved.biz_name!r} competitors={saved.competitors!r}",
                )

            # Stage 3: GET /sites/{tenant_id} -- check actual field content,
            # not just status code.
            site = client.get(f"/sites/{tenant_id}")
            check("3. GET /sites/{tenant_id} returns 200", site.status_code == 200, site.text)
            site_body = site.json() if site.status_code == 200 else {}

            check(
                "3b. real submitted content is present",
                site_body.get("biz_name") == "Desert Pro Plumbing"
                and site_body.get("rating_value") == 4.9,
                site_body,
            )

            internal_fields_that_must_never_leak = (
                "lead_routing", "approver", "timeline", "notes", "extra_pages",
                "assets_status", "has_site", "site_url", "site_platform",
                "site_issues", "has_logo", "brand_colors", "inspo_sites",
                "brand_words", "fsm_system", "booking_system", "has_gbp",
                "competitors",  # <-- see CLAUDE.md addendum: this one currently DOES leak
            )
            leaked = [f for f in internal_fields_that_must_never_leak if f in site_body]
            check(
                "3c. no internal-only field leaks into the public response",
                not leaked,
                f"leaked fields: {leaked}" if leaked else "",
            )

            # Stage 4: /chat works end-to-end with no real Grok credentials
            # configured -- should degrade gracefully to NullVoiceBackend's
            # fixed reply, not 500.
            chat = client.post("/chat", json={"tenant_id": tenant_id, "message": "Do you serve Tempe?"})
            check("4. POST /chat returns 200 with no voice backend configured", chat.status_code == 200, chat.text)
            if chat.status_code == 200:
                reply = chat.json().get("reply", "")
                check("4b. reply is the expected Null-backend fallback text, not an error", "not fully set up" in reply.lower(), reply)

            # Stage 5: the widget file the Lovable frontend embeds actually
            # exists, is a real implementation, and its request shape
            # matches what /chat expects.
            widget_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "webstaffr", "workers", "angel", "widget", "angel-widget.js",
            )
            widget_exists = os.path.isfile(widget_path)
            check("5. angel-widget.js exists", widget_exists, widget_path)
            if widget_exists:
                widget_src = open(widget_path).read()
                check(
                    "5b. widget isn't a stub (posts to /chat with tenant_id+message)",
                    '"/chat"' in widget_src and "tenant_id" in widget_src and "message" in widget_src,
                )
    finally:
        os.remove(db_path)

    print()
    if FAILURES:
        print(f"{len(FAILURES)} check(s) failed:")
        for f in FAILURES:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print("All checks passed.")


if __name__ == "__main__":
    main()
