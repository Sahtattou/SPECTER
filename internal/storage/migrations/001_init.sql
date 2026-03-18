CREATE TABLE IF NOT EXISTS threat_records (
    event_id TEXT PRIMARY KEY,
    ioc_value TEXT NOT NULL,
    ioc_type TEXT NOT NULL,
    source_name TEXT NOT NULL,
    source_url TEXT NOT NULL DEFAULT '',
    source_query TEXT NOT NULL DEFAULT '',
    raw_evidence_json TEXT NOT NULL DEFAULT '{}',
    collected_at DATETIME NOT NULL,
    corroboration_count INTEGER NOT NULL DEFAULT 0,
    open_ports_json TEXT NOT NULL DEFAULT '[]',
    asn TEXT NOT NULL DEFAULT '',
    is_synthetic INTEGER NOT NULL DEFAULT 0,
    poison_attack_type TEXT NOT NULL DEFAULT '',
    poison_detected INTEGER NULL,
    detection_rule TEXT NOT NULL DEFAULT '',
    composite_score REAL NULL,
    threat_level TEXT NOT NULL DEFAULT '',
    days_to_attack TEXT NOT NULL DEFAULT '',
    pipeline_stage TEXT NOT NULL DEFAULT 'ingested',
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_threat_records_stage
    ON threat_records(pipeline_stage);

CREATE INDEX IF NOT EXISTS idx_threat_records_ioc
    ON threat_records(ioc_type, ioc_value);

CREATE INDEX IF NOT EXISTS idx_threat_records_collected_at
    ON threat_records(collected_at);
