package models

import "time"

type ThreatRecord struct {
	Source      string                 `json:"source"`
	Target      string                 `json:"target"` //IP or domain
	Confidence  int                    `json:"confidence"`
	IsMalicious bool                   `json:"is_malicious"`
	LastSeen    time.Time              `json:"last_seen"`
	Details     map[string]interface{} `json:"details"`
}

type ThreatEvent struct {
	EventID            string
	IOCValue           string
	IOCType            string
	SourceName         string
	SourceURL          string
	SourceQuery        string
	RawEvidenceJSON    string
	CollectedAt        time.Time
	CorroborationCount int
	OpenPorts          []int
	ASN                *string
	IsSynthetic        bool
	PoisonAttackType   *string
	PoisonDetected     *bool
	DetectionRule      *string
	CompositeScore     *float64
	ThreatLevel        *string
	DaysToAttack       *string
	PipelineStage      string
}
