"""FastAPI router for client intake -- the first stage of the intake ->
generated customer site -> Angel widget MVP flow (CLAUDE.md / PROJECT.md).

Mounted into the main app via create_app().include_router(intake_router)
in webstaffr/workers/angel/router.py, keeping that file's own router
Angel-specific per its existing docstring.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from .attribution import TrackingNumberRepository
from .db import DB_ERRORS, get_connection
from .intake import (
    IntakeRepository,
    IntakeSubmission,
    IntakeValidationError,
    generate_tenant_id,
    validate_intake_payload,
)
from .trade_presets import SUPPORTED_INDUSTRIES, get_preset

intake_router = APIRouter()


class IntakeRequest(BaseModel):
    # Section 1: Business Basics
    biz_name: str
    phone: str
    email: str
    industry: str
    service_area: str
    years_in_biz: Optional[int] = None
    emergency_service: Optional[str] = None

    # Section 2: Current Web Presence
    has_site: Optional[str] = None
    site_url: Optional[str] = None
    site_platform: Optional[str] = None
    site_issues: Optional[str] = None
    has_gbp: Optional[str] = None
    gbp_url: Optional[str] = None
    google_review_link: Optional[str] = None

    # Section 3: Brand
    has_logo: Optional[str] = None
    brand_colors: Optional[str] = None
    brand_words: Optional[str] = None
    inspo_sites: Optional[str] = None

    # Section 4: Positioning
    tagline: str
    differentiator: str
    competitors: Optional[str] = None
    tone: Optional[str] = None

    # Section 5: Services
    services: list[str]
    pricing_shown: Optional[str] = None
    promos: Optional[str] = None
    license_number: str

    # Section 6: Proof & Credibility
    rating_value: Optional[float] = None
    review_count: Optional[int] = None
    certifications: Optional[str] = None
    has_before_after: Optional[str] = None
    testimonials: Optional[str] = None

    # Section 7: Social & Tools
    facebook_url: Optional[str] = None
    instagram_url: Optional[str] = None
    fsm_system: Optional[str] = None
    booking_system: Optional[str] = None

    # Section 8: Workforce Plan
    plan: str
    lead_routing: str
    timeline: Optional[str] = None
    approver: str

    # Section 9: Content & SEO
    assets_status: Optional[str] = None
    keywords: Optional[str] = None
    extra_pages: Optional[str] = None
    notes: Optional[str] = None


class IntakeResponse(BaseModel):
    submission_id: int
    tenant_id: str
    biz_name: str
    industry: str
    plan: str


def _get_connection(request: Request):
    """Reads the db_path the app was created with (create_app stores it on
    app.state) rather than importing a module-level default -- keeps this
    router testable against whatever database a given app instance uses.
    Backend (SQLite vs Postgres) is chosen by db.get_connection() based on
    DATABASE_URL -- this router doesn't need to know which one it got.
    Raises HTTPException(503) on a DB-layer failure instead of letting a
    raw psycopg2/sqlite3 exception propagate to the client."""
    try:
        return get_connection(request.app.state.db_path)
    except DB_ERRORS as exc:
        raise HTTPException(status_code=503, detail="Intake temporarily unavailable -- please try again shortly") from exc


@intake_router.post("/intake", response_model=IntakeResponse)
def submit_intake(req: IntakeRequest, request: Request) -> IntakeResponse:
    data = req.model_dump()

    try:
        validate_intake_payload(data)
    except IntakeValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    tenant_id = generate_tenant_id(req.biz_name)
    submission = IntakeSubmission.from_payload(tenant_id, data)

    conn = _get_connection(request)
    try:
        repo = IntakeRepository(conn)
        repo.save(submission)
        # Every tenant gets a tracking number the moment they have a real
        # site to point it at -- get_or_create() is idempotent, so a
        # resubmission for the same tenant_id (there isn't one today, but
        # nothing here assumes there never will be) can't create a second
        # one. See attribution.py's module docstring for why this isn't a
        # real phone number yet.
        TrackingNumberRepository(conn).get_or_create(tenant_id)
        conn.commit()
    finally:
        conn.close()

    return IntakeResponse(
        submission_id=submission.submission_id,
        tenant_id=tenant_id,
        biz_name=submission.biz_name,
        industry=submission.industry,
        plan=submission.plan,
    )


@intake_router.get("/intake/presets")
def list_presets() -> dict:
    """All supported industries, for populating the intake form's industry
    selector without hardcoding the list on the Lovable/frontend side."""
    return {"industries": SUPPORTED_INDUSTRIES}


@intake_router.get("/intake/presets/{industry}")
def industry_preset(industry: str) -> dict:
    """Per-trade hint text and FSM software options for one industry.
    Always resolves (falls back to 'Other') -- see trade_presets.get_preset."""
    return get_preset(industry)
