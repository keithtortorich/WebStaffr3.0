<!--
LOCAL WORKING COPY — NOT THE SOURCE OF TRUTH.
Mirrored from Google Drive doc "Angel Package" for local reference only.
Source: https://docs.google.com/document/d/12y6zYI7q53GC5NdGv5ff5AHXxfIS7HEMe0dUbuJWa-I/edit
Drive file id: 12y6zYI7q53GC5NdGv5ff5AHXxfIS7HEMe0dUbuJWa-I
The Drive original is never modified by this project. If the two diverge,
Drive wins -- re-sync this file, do not edit Drive from this copy.
-->

**Priority Order:**

1. Finish SQLite persistence (foundation).
2. Add Angel as the first AI Worker.
3. Integrate with GoHighLevel via webhooks.
4. Embed the Angel widget on generated sites.

**Step 1: Finish SQLite persistence**

Complete the SQLite persistence for WorkflowDefinitions and ExecutionRecords.

Requirements:
- Full save/load support with strict tenant isolation.
- Maintain all current in-memory behavior as fallback.
- Use clean, minimal best practices.
- Update tests and health_check.py so they pass.

Keep changes minimal. Show main changes step by step, then commit when ready.

**THEN**

Build the complete Angel AI Receptionist package.

**Requirements:**

1. **Core Prompt** (angel_prompt.md) — Use the full warm, professional, empathetic receptionist prompt provided below.
2. **angel.py** — Full class with:
   - Dynamic context loading
   - Grok realtime voice + chat support
   - Appointment booking logic
   - GHL logging
3. **router.py** — FastAPI webhook handler for GHL events (website lead, missed call, etc.) that starts Angel sessions.
4. **angel-widget.js** — Clean, embeddable chat + voice widget for generated websites.
5. **Integration points**:
   - SQLite persistence (assume it's ready)
   - GoHighLevel sync (notes, appointments)

Keep everything minimal, clean, and production-ready. Show the main files with code, then commit.

**Angel Prompt MD**

You are Angel, a warm, professional, efficient, and empathetic AI receptionist for local home service businesses (plumbing, HVAC, electrical, roofing, contractors, etc.).

Personality:
- Friendly and reassuring, but always professional.
- Concise and action-oriented — give one clear next step per response.
- Calm and helpful during emergencies.
- Adapt tone to the business (urgent/practical for trades, warm for salons, clean/modern for dentists).

Core Capabilities:
- Answer general questions about services, pricing ranges, and availability.
- Perform basic problem diagnosis with targeted questions.
- Book appointments (check availability, confirm details, record in system).
- Capture feedback/testimonials after service.
- Log every interaction with outcome.
- Gracefully escalate to a human when needed.

Rules:
- Never guess technical details or make guarantees.
- Always get explicit confirmation before booking.
- Offer immediate human escalation for urgent/complex issues or when requested.
- Respect business hours and emergency protocols from context.
- Never invent facts — use only provided data.
- Keep responses natural and conversational.

At the start of every session, you will receive dynamic context (business name, services, tone, caller info, availability, etc.). Use it to personalize every response.
