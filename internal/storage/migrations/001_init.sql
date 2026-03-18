-- Initial schema scaffold for SPECTER storage.
CREATE TABLE IF NOT EXISTS threat_events (
    event_id TEXT PRIMARY KEY,
    ioc_value TEXT NOT NULL,
    ioc_type TEXT NOT NULL,
    source_name TEXT NOT NULL,
    collected_at TIMESTAMP NOT NULL
);
