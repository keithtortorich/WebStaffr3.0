-- 0001_initial.sql
-- Tenant-scoped tables for WorkflowDefinition and ExecutionRecord persistence.
-- Every table carries tenant_id explicitly; nothing is queried without it.

CREATE TABLE IF NOT EXISTS tenants (
    tenant_id TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS workflow_definitions (
    tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id),
    workflow_id TEXT NOT NULL,
    step_names TEXT NOT NULL,   -- JSON array of step names, in execution order
    created_at TEXT NOT NULL,
    PRIMARY KEY (tenant_id, workflow_id)
);

CREATE INDEX IF NOT EXISTS idx_workflow_definitions_tenant
    ON workflow_definitions(tenant_id);

CREATE TABLE IF NOT EXISTS execution_records (
    execution_id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id TEXT NOT NULL,
    workflow_id TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at REAL NOT NULL,
    finished_at REAL,
    steps_json TEXT NOT NULL,  -- JSON array of step traces (input/output/status/timestamps)
    FOREIGN KEY (tenant_id, workflow_id) REFERENCES workflow_definitions(tenant_id, workflow_id)
);

CREATE INDEX IF NOT EXISTS idx_execution_records_tenant
    ON execution_records(tenant_id);

CREATE INDEX IF NOT EXISTS idx_execution_records_tenant_workflow
    ON execution_records(tenant_id, workflow_id);
