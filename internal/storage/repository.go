package storage

import (
	"database/sql"
	"log"

	"github.com/Sahtattou/SPECTER/pkg/models"
	_ "github.com/mattn/go-sqlite3"
)

type Repository struct {
	DB *sql.DB
}

func InitDB(filepath string) (*Repository, error) {
	db, err := sql.Open("sqlite3", filepath)
	if err != nil {
		return nil, err
	}

	createTableQuery := `
	CREATE TABLE IF NOT EXISTS iocs (
		ioc_uuid TEXT PRIMARY KEY, raw_value TEXT, ioc_type TEXT,
		source_name TEXT, source_url TEXT, source_query TEXT, 
		raw_evidence TEXT, collected_at DATETIME, pipeline_stage TEXT,
		is_synthetic BOOLEAN, poison_attack_type TEXT, poison_detected BOOLEAN,
		detection_rule TEXT, corroboration_count INTEGER, domain_age_days INTEGER,
		open_ports TEXT, asn TEXT, composite_score REAL, score_breakdown TEXT,
		days_to_attack_estimate TEXT, threat_level TEXT, analyst_notes TEXT
	);`

	_, err = db.Exec(createTableQuery)
	if err != nil {
		return nil, err
	}

	return &Repository{DB: db}, nil
}

func (r *Repository) Save(env *models.IOCEnvelope) error {
	query := `
	INSERT INTO iocs (
		ioc_uuid, raw_value, ioc_type, source_name, source_url, source_query,
		raw_evidence, collected_at, pipeline_stage, is_synthetic,
		corroboration_count, open_ports, score_breakdown
	) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`

	_, err := r.DB.Exec(query,
		env.IOCUUID, env.RawValue, env.IOCType, env.SourceName, env.SourceURL, env.SourceQuery,
		env.RawEvidence, env.CollectedAt, env.PipelineStage, env.IsSynthetic,
		env.CorroborationCount, env.OpenPorts, env.ScoreBreakdown,
	)

	if err != nil {
		log.Printf("Failed to save IOC: %v", err)
		return err
	}
	return nil
}
