# WebStaffr — MVP Overview

## What it is

WebStaffr is an AI workforce platform for local service businesses. The product sits on three web properties:

1. **WebStaffr.com** — main product site: positioning, intake, pricing, signup.
2. **Trade example sites** — example customer sites embedded within WebStaffr's domain, showing what a generated site looks like for HVAC, plumbing, electrical, etc.
3. **Investor forward site** — standalone investor-facing site for fundraising and pitch material.

The backend and Lovable-generated customer site are already live under the canonical Lovable "Site Weaver" project. This docs layer now reflects the current product direction.

## The three-site structure

### Site 1 — WebStaffr.com
- Business-facing main site
- Product positioning, workforce plan descriptions, intake entry point
- Angel widget embedded for live demos / questions
- Links to trade examples

### Site 2 — Trade example sites
- Real example sites for each trade vertical, hosted within WebStaffr's domain
- Used as proof points during sales conversations
- Populated from real `IntakeSubmission` data or curated demo data
- AI chat concierge embedded on each example
- No fabricate-fill policy: only real or explicitly labeled demo data

### Site 3 — Investor forward site
- Standalone, separate identity from the commercial site
- Investor-grade material: updated projections, unit economics, product overview, team, risks, ask
- Not confused with the customer-facing site

## How it connects to what is already built

| Component | Status |
|---|---|
| Intake + backend (`POST /intake`, `GET /sites/{tenant_id}`) | Live, verified end-to-end |
| Lovable "Site Weaver" multi-tenant frontend | Live, rendering real data |
| Angel chat widget | Embedded, powered by Grok, verified live |
| Voice (Retell) | Built, not yet exercised against a real phone |
| GHL CRM sync | Built, deliberately not connected yet (trial-timing call) |

## Design principles

- Perfect-site principle: never fabricate reviews, ratings, or testimonials. Omit missing data.
- Privacy by default: internal-only intake fields never reach public-facing sites.
- ServiceTitan/Jobber/Housecall Pro etc. are baseline environment, not add-ons. Being on one of them is a qualification signal, not an upgrade trigger.
- Office Staff is the core plan: free 30 days with a generated site, then $497/mo to keep it.

## Where the real state lives

- `TASKS.md` — live status, what is done vs open, updated every session
- `CLAUDE.md` — full decision history, dated and append-only
- `CREDENTIALS.md` — env vars and why (never values)
- `STRATEGY.md` — pricing, positioning, and beachhead strategy
