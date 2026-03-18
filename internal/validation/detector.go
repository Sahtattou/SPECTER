package validation

import (
	"strings"

	"github.com/Sahtattou/SPECTER/pkg/models"
)

const (
	RuleSingleSourceFreshDomain = "SINGLE_SOURCE_FRESH_DOMAIN"
	RuleSuspiciousTimestamp     = "SUSPICIOUS_TIMESTAMP"
	RuleTTPBannerMismatch       = "TTP_BANNER_MISMATCH"
)

func Detect(rec models.ThreatRecord) models.ThreatRecord {
	quarantine := false
	rule := ""

	if rec.IOCType == "domain" && rec.CorroborationCount <= 1 {
		quarantine = true
		rule = RuleSingleSourceFreshDomain
	}

	if strings.TrimSpace(rec.RawEvidenceJSON) == "" {
		quarantine = true
		if rule == "" {
			rule = RuleSuspiciousTimestamp
		}
	}

	if quarantine {
		d := true
		rec.PoisonDetected = &d
		rec.DetectionRule = rule
		rec.PipelineStage = "quarantined"
	} else {
		rec.PipelineStage = "validated"
	}

	return rec
}
