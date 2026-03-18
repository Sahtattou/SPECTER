package models

import "time"

type Threat struct {
	IOCValue         string                 `json:"ioc_value"`
	IOCType          string                 `json:"ioc_type"`
	SourceName       string                 `json:"source_name"`
	SourceURL        string                 `json:"source_url"`
	SourceQuery      string                 `json:"source_query"`
	RawEvidence      map[string]any         `json:"raw_evidence,omitempty"`
	CollectedAt      time.Time              `json:"collected_at"`
	OpenPorts        []int                  `json:"open_ports,omitempty"`
	ASN              string                 `json:"asn,omitempty"`
	Tags             []string               `json:"tags,omitempty"`
	Attributes       map[string]interface{} `json:"attributes,omitempty"`
	Corroboration    int                    `json:"corroboration,omitempty"`
	IsSynthetic      bool                   `json:"is_synthetic"`
	PoisonAttackType string                 `json:"poison_attack_type,omitempty"`
}

type ThreatRecord struct {
	EventID            string    `json:"event_id"`
	IOCValue           string    `json:"ioc_value"`
	IOCType            string    `json:"ioc_type"`
	SourceName         string    `json:"source_name"`
	SourceURL          string    `json:"source_url"`
	SourceQuery        string    `json:"source_query"`
	RawEvidenceJSON    string    `json:"raw_evidence_json"`
	CollectedAt        time.Time `json:"collected_at"`
	CorroborationCount int       `json:"corroboration_count"`
	OpenPorts          []int     `json:"open_ports,omitempty"`
	ASN                string    `json:"asn,omitempty"`
	IsSynthetic        bool      `json:"is_synthetic"`
	PoisonAttackType   string    `json:"poison_attack_type,omitempty"`
	PoisonDetected     *bool     `json:"poison_detected,omitempty"`
	DetectionRule      string    `json:"detection_rule,omitempty"`
	CompositeScore     *float64  `json:"composite_score,omitempty"`
	ThreatLevel        string    `json:"threat_level,omitempty"`
	DaysToAttack       string    `json:"days_to_attack,omitempty"`
	PipelineStage      string    `json:"pipeline_stage,omitempty"`
	CreatedAt          time.Time `json:"created_at"`
	UpdatedAt          time.Time `json:"updated_at"`
}
