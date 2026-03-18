
CREATE TABLE IF NOT EXISTS threat_events (
    event_id TEXT PRIMARY KEY,
    ioc_value TEXT NOT NULL,
    ioc_type TEXT NOT NULL,
    source_name TEXT,
    source_url TEXT,
    source_query TEXT,
    raw_evidence_json TEXT,
    collected_at DATETIME NOT NULL,
    corroboration_count INTEGER DEFAULT 1,
    open_ports TEXT,
    asn TEXT,
    is_synthetic BOOLEAN DEFAULT FALSE,
    poison_attack_type TEXT,
    poison_detected BOOLEAN,
    detection_rule TEXT,
    composite_score REAL,
    threat_level TEXT,
    days_to_attack TEXT,
    pipeline_stage TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_pipeline_stage ON threat_events(pipeline_stage);
CREATE INDEX IF NOT EXISTS idx_collected_at ON threat_events(collected_at DESC);
