# PROJECT.md — WebStaffr

## Product Vision
WebStaffr is an AI employee platform: an extension of a business's team through configurable AI workers, not a bundle of point automations. The product should read as workforce, not tooling.

## Target Users
- Small and mid-sized service businesses (SMBs) — the core end-customer.
- Agencies and resellers who deploy and manage WebStaffr on behalf of their own clients.
- Individual operators who want additional staffing coverage without adding headcount.

## Core Value Proposition
An AI workforce layer that takes on the recurring, people-shaped work of running a business — answering, following up, coordinating, following through — so an operator gets employee-equivalent coverage without growing payroll. The value is staffing, not software features.

## High-Level Capabilities (abstract)
- Voice — handling and responding to calls.
- Chat — handling text-based conversation.
- Workflows — coordinating multi-step business processes.
- Integrations — connecting into the tools a business already uses.

## Business Intent — What Success Looks Like
- Operators experience WebStaffr as reliable staff, not administered software.
- Customers expand from a single AI worker to a fuller AI workforce over time.
- Agencies can resell and white-label the platform to their own client base.
- Retention is driven by trust in coverage, not by lock-in.

## Non-Technical Roadmap Themes
- **Depth** — growing from one AI worker to a multi-role AI workforce per customer.
- **Breadth** — expanding the range of business functions covered.
- **Trust** — building operator confidence in autonomous, unsupervised action.
- **Channel** — direct-to-business and agency-mediated distribution as parallel paths to market.

## MVP Scope (this repo)
Full flow: intake → generated customer site → Angel widget embedded and working. Frontend/site-generation is delegated to Lovable; this repo owns backend logic (Angel, tenant isolation, GHL/voice integration, executor engine, tests).
