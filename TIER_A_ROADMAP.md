# Tier A Roadmap — WebStaffr vs. SiteWork Agency

Source: a competitor analysis of SiteWork Agency (bundled AI-voice + lead-gen-site + reviews + GBP, $597/mo flat, money-back guarantee) plus an earlier 3-phase/20-week execution plan someone derived from its recommendations. This doc corrects that plan against WebStaffr's actual build state as of 2026-07-12 and flags what's real work vs. what needs your own business/legal judgment.

## Read on SiteWork Agency `[Inference]`

They're running the same wedge WebStaffr is aimed at. Two things worth taking seriously from their own flagged weaknesses, because they apply to us too:
- **Guarantee refund exposure if results lag 60–90 days.** Don't promise "pays for itself" publicly until there's a real way to back it (see attribution, below).
- **Single-vendor AI voice risk** (quality/hallucination/cost swings). We have the same exposure today — Retell + Grok only, no fallback.

Their edge is bundling vs. fragmented point-tools. WebStaffr's potential edge on top of that: a genuinely multi-tenant architecture (confirmed this session — one Lovable template serves every customer, no per-site build cost), so unit economics scale better than an agency re-doing a site per client.

**Correction to the original Tier-A plan:** it lists "Jobber API integration" as blocking the HVAC soft launch. That's SiteWork's own proposed *Enterprise-tier* idea (Jobber/ServiceTitan/Housecall Pro), not a dependency either company has built. WebStaffr's actual CRM integration is **GoHighLevel** (`webstaffr/workers/angel/ghl.py`), already coded. HVAC soft launch doesn't need Jobber — GHL already covers CRM sync. If a Jobber (or ServiceTitan/Housecall Pro) integration is wanted later for an Enterprise tier, it's new scope: same `Protocol` + `Null*` + real-impl shape as the GHL/Retell integrations, not a blocker for anything already planned.

## Reality check: Phase 1 is further along than the original plan assumed

The original Phase 1 ("Validation + architecture + legal, weeks 1–6, no customer impact yet") predates today. As of 2026-07-12, confirmed live in production: intake → generated site → live Grok chat works end-to-end (`TASKS.md` #28–#30). Retell voice is built but not yet exercised against a real Retell account/phone number. GHL is coded but deliberately not connected — your call on trial timing, unchanged. So the architecture leg of Phase 1 is effectively done; what's left of Phase 1 is genuinely the legal/guarantee-structuring piece.

## Revised phases

| Phase | Focus | Status |
|---|---|---|
| 1 | Architecture | **Done** — intake/site/chat live in prod, verified today. |
| 1 | Legal sign-off on guarantee | **Not started — needs your counsel, not delegable to me.** |
| 2 | Attribution/dashboard (call tracking, lead source) | **Not built.** Real net-new work: per-tenant tracking numbers, an events schema, a dashboard surface. Scope-able the same way `/intake`/`/sites` were built. |
| 2 | HVAC soft launch | Ready to attempt once you're comfortable — nothing technical blocks it; GHL wiring is optional, not required. |
| 3 | Plumbing/electrical vertical content | Presentation-layer work only (`trade_presets.py` already has the hook — same pattern as HVAC, just more `TRADE_HINTS`/`INDUSTRY_SOFTWARE` entries). Low effort once one vertical is proven. |
| 3 | Voice failover (multi-vendor) | **Not built.** Real gap, matches SiteWork's own flagged weakness. Same `Protocol`+`Null*` shape as existing integrations — a second `VoiceBackend` implementation plus a failover policy. |
| 3 | Enterprise CRM integrations (Jobber/ServiceTitan/etc.) | New scope, not currently planned or blocking anything. |

## What I can actually build vs. what's yours

**Can build**, same patterns already established in this codebase: attribution/call-tracking schema + endpoints, tiering logic, a second voice-backend integration for failover, additional vertical presets, a new CRM integration if you want one beyond GHL.

**Can't do:** legal review of a money-back guarantee, actual pricing decisions, GTM/marketing execution, or ARPU/CAC projections — any dollar figure in this space would be `[Inference]` with no real data behind it, not something I'll present as fact.

**Next concrete step, if you want one:** attribution/call-tracking is the one item that's both real engineering work and directly unblocks the guarantee conversation (can't back "pays for itself" without it). Say the word and I'll scope it the way `/intake` got scoped — migration, endpoint, tests — as a queued item for Hermes this week.
