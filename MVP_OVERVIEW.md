# WebStaffr — MVP Overview

## What it is

A platform that takes a local service business (HVAC, plumbing, electrical, etc.) from a filled-out form to a live, branded website with an AI concierge answering visitor questions and capturing leads 24/7 — no web developer, no missed calls.

## The MVP flow

```
Intake  →  Generated site  →  Angel widget (embedded, working)
```

1. **Intake** — the business owner fills out a structured form (9 sections, ~35 fields: basics, web presence, brand, positioning, services, proof/credibility, social/tools, workforce plan, content/SEO). Backend: `POST /intake`.
2. **Generated site** — the backend serves a curated, public-safe projection of that data (`GET /sites/{tenant_id}`). Frontend: Lovable "Site Weaver," one dynamic app that renders any tenant by ID — not one site built per customer.
3. **Angel widget** — an AI chat concierge (voice-capable, not yet live-tested) embedded on the generated site, answering questions and capturing leads. Backed by xAI's Grok.

**Status: all three steps verified working end-to-end in production as of 2026-07-13.**

## Architecture at a glance

| Layer | What |
|---|---|
| Backend | FastAPI (Python), raw SQL (no ORM) |
| Persistence | Dual-backend: SQLite for local dev/tests, Postgres (Supabase) in production |
| Hosting | Vercel, serverless functions |
| Frontend | Lovable-hosted, multi-tenant single app (not per-customer sites) |
| Chat AI | xAI Grok |
| Voice AI | Retell AI (built, not yet exercised against a real phone number) |
| CRM sync | GoHighLevel (built, deliberately not connected yet) |

## Design principles baked into the build

- **Perfect-site principle:** never fabricate a rating, review, or testimonial. Omit a section when the data isn't there — don't invent filler.
- **Privacy by default:** internal-only intake fields (who routes leads, license numbers, competitor notes) never reach the public site; enforced by tests, not just code review.
- **Integration pattern:** every third-party integration (Retell, GHL, Grok) follows the same shape — a `Protocol` interface, a safe `Null*` default, and a real implementation that fails loudly if misconfigured. No integration is silently half-built.

## What's deliberately not in MVP scope

- Pricing tiers, a money-back guarantee, or attribution/call-tracking dashboards — scoped as future work, not built (see `TIER_A_ROADMAP.md`).
- GHL CRM sync — built and ready, but not connected (founder's own call on when to start the trial clock).
- Live-verified voice calls — Retell integration exists, hasn't taken a real call yet.
- Formal user auth, CI/CD pipeline, multi-region/production-scale hardening beyond what's documented in `CLAUDE.md`.

## Where the real state lives

- `TASKS.md` — live status, what's done vs. open, updated every session.
- `CLAUDE.md` — full decision history, dated and append-only.
- `CREDENTIALS.md` — what env vars exist and why (never values).
- `TIER_A_ROADMAP.md` — future business-model/feature roadmap, reconciled against actual build state.
