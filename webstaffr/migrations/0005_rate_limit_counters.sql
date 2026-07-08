-- 0005_rate_limit_counters.sql
-- Fixed-window request counters for per-tenant, per-endpoint rate limiting
-- (webstaffr/rate_limit.py), added 2026-07-08 per CODE_REVIEW.md's High
-- finding: /chat and /webhooks/ghl had no rate limiting, and GROK_API_KEY
-- is now live in production -- an unauthenticated caller could otherwise
-- run up real, billed xAI usage with no ceiling.
--
-- Deliberately not tenant-scoped via a foreign key to tenants(tenant_id)
-- like every other table in this schema: rate limiting must work even
-- against a guessed/never-registered tenant_id (that's exactly the attack
-- this closes), so an FK constraint that could reject the insert would
-- defeat the purpose. This table is a pure counter/log, not a domain
-- record.
--
-- Note (2026-07-08): this is migration 0005 with no 0004 file present --
-- 0004 (RLS default-deny) was applied directly to the live Supabase
-- project and was never committed as a file here, a separate, already-
-- flagged gap (CODE_REVIEW.md action item #4, not fixed by this
-- migration). migrate()'s applied-files check (db.py) applies whatever
-- .sql files exist by sorted filename, regardless of numeric contiguity,
-- so this gap does not affect SQLite migration behavior -- flagging it
-- here only so the numbering gap isn't mistaken for an accident.

CREATE TABLE IF NOT EXISTS rate_limit_counters (
    tenant_id TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    window_start INTEGER NOT NULL,  -- unix timestamp, floored to the window size
    request_count INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (tenant_id, endpoint, window_start)
);
