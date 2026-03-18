package storage

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"os"

	"github.com/Sahtattou/SPECTER/pkg/models"
	_ "github.com/mattn/go-sqlite3"
)

type Repository struct {
	DB *sql.DB
}

func InitDB(dbPath string, migrationPath string) (*Repository, error) {
	db, err := sql.Open("sqlite3", dbPath)
	if err != nil {
		return nil, fmt.Errorf("failed to open database: %w", err)
	}

	migrationSQL, err := os.ReadFile(migrationPath)
	if err != nil {
		return nil, fmt.Errorf("failed to read migration file %s: %w", migrationPath, err)
	}

	_, err = db.Exec(string(migrationSQL))
	if err != nil {
		return nil, fmt.Errorf("failed to execute migration: %w", err)
	}

	log.Println("[*] Database initialized and migrations applied successfully.")
	return &Repository{DB: db}, nil
}

func (r *Repository) Save(event *models.ThreatEvent) error {
	query := `
	INSERT INTO threat_events (
		event_id, ioc_value, ioc_type, source_name, source_url, source_query,
		raw_evidence_json, collected_at, corroboration_count, open_ports, asn,
		is_synthetic, poison_attack_type, poison_detected, detection_rule,
		composite_score, threat_level, days_to_attack, pipeline_stage
	) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`

	portsJSON, _ := json.Marshal(event.OpenPorts)

	_, err := r.DB.Exec(query,
		event.EventID, event.IOCValue, event.IOCType, event.SourceName,
		event.SourceURL, event.SourceQuery, event.RawEvidenceJSON, event.CollectedAt,
		event.CorroborationCount, string(portsJSON), event.ASN,
		event.IsSynthetic, event.PoisonAttackType, event.PoisonDetected, event.DetectionRule,
		event.CompositeScore, event.ThreatLevel, event.DaysToAttack, event.PipelineStage,
	)

	if err != nil {
		log.Printf("[-] Failed to save ThreatEvent %s: %v", event.EventID, err)
		return err
	}

	return nil
}
