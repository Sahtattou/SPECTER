package models

import "time"

type IOCEnvelope struct {
	IOCUUID  string `json:"ioc_uuid" db:"ioc_uuid"`
	RawValue string `json:"raw_value" db:"raw_value"`
	IOCType  string `json:"ioc_type" db:"ioc_type"`

	SourceName  string    `json:"source_name" db:"source_name"`
	SourceURL   string    `json:"source_url" db:"source_url"`
	SourceQuery string    `json:"source_query" db:"source_query"`
	RawEvidence string    `json:"raw_evidence" db:"raw_evidence"`
	CollectedAt time.Time `json:"collected_at" db:"collected_at"`

	PipelineStage string `json:"pipeline_stage" db:"pipeline_stage"`

	IsSynthetic      bool    `json:"is_synthetic" db:"is_synthetic"`
	PoisonAttackType *string `json:"poison_attack_type" db:"poison_attack_type"`
	PoisonDetected   *bool   `json:"poison_detected" db:"poison_detected"`
	DetectionRule    *string `json:"detection_rule" db:"detection_rule"`

	CorroborationCount int     `json:"corroboration_count" db:"corroboration_count"`
	DomainAgeDays      *int    `json:"domain_age_days" db:"domain_age_days"`
	OpenPorts          string  `json:"open_ports" db:"open_ports"`
	ASN                *string `json:"asn" db:"asn"`

	CompositeScore       *float64 `json:"composite_score" db:"composite_score"`
	ScoreBreakdown       string   `json:"score_breakdown" db:"score_breakdown"`
	DaysToAttackEstimate *string  `json:"days_to_attack_estimate" db:"days_to_attack_estimate"`
	ThreatLevel          *string  `json:"threat_level" db:"threat_level"`

	AnalystNotes *string `json:"analyst_notes" db:"analyst_notes"`
}
