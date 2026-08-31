-- Forward-compatible migration for deployments using an external migration runner.
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    session_id INTEGER,
    actor_id INTEGER,
    payload TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_audit_logs_session_id ON audit_logs(session_id);
