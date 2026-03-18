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
