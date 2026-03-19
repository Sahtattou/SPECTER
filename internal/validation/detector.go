package validation

import (
	"encoding/json"
	"strconv"
	"strings"
	"time"

	"github.com/Sahtattou/SPECTER/pkg/models"
)

const (
	RuleSingleSourceFreshDomain = "SINGLE_SOURCE_FRESH_DOMAIN"
	RuleSuspiciousTimestamp     = "SUSPICIOUS_TIMESTAMP"
	RuleTTPBannerMismatch       = "TTP_BANNER_MISMATCH"
)

func Detect(rec models.ThreatRecord) models.ThreatRecord {
	if rule, quarantined := detectRule(rec); quarantined {
		d := true
		rec.PoisonDetected = &d
		rec.DetectionRule = rule
		rec.PipelineStage = "quarantined"
	} else {
		d := false
		rec.PoisonDetected = &d
		rec.DetectionRule = ""
		rec.PipelineStage = "validated"
	}

	return rec
}

func detectRule(rec models.ThreatRecord) (string, bool) {
	if ruleSingleSourceFreshDomain(rec) {
		return RuleSingleSourceFreshDomain, true
	}
	if ruleTTPBannerMismatch(rec) {
		return RuleTTPBannerMismatch, true
	}
	if ruleSuspiciousTimestamp(rec) {
		return RuleSuspiciousTimestamp, true
	}
	return "", false
}

func ruleSingleSourceFreshDomain(rec models.ThreatRecord) bool {
	if rec.CorroborationCount > 1 {
		return false
	}
	if rec.IOCType != "domain" {
		return false
	}
	domainAge, ok := extractDomainAgeDays(rec.RawEvidenceJSON)
	if !ok {
		return false
	}
	return domainAge < 7
}

func ruleSuspiciousTimestamp(rec models.ThreatRecord) bool {
	if isEffectivelyEmptyEvidence(rec.RawEvidenceJSON) {
		return true
	}

	if rec.CollectedAt.IsZero() || rec.CreatedAt.IsZero() {
		return false
	}
	if time.Since(rec.CollectedAt) <= 20*24*time.Hour {
		return false
	}
	if time.Since(rec.CreatedAt) > 24*time.Hour {
		return false
	}
	return true
}

func isEffectivelyEmptyEvidence(rawEvidence string) bool {
	v := strings.TrimSpace(strings.ToLower(rawEvidence))
	if v == "" {
		return true
	}
	return v == "{}" || v == "null" || v == "[]"
}

func ruleTTPBannerMismatch(rec models.ThreatRecord) bool {
	if rec.IOCType != "ip" {
		return false
	}

	hasC2Port := false
	for _, p := range rec.OpenPorts {
		switch p {
		case 50050, 40056, 8888, 4444:
			hasC2Port = true
		}
	}
	if !hasC2Port {
		return false
	}

	evidence := strings.ToLower(rec.RawEvidenceJSON)
	for _, brand := range []string{"cloudflare", "akamai", "fastly", "amazon", "azure", "google"} {
		if strings.Contains(evidence, brand) {
			return true
		}
	}
	return false
}

func extractDomainAgeDays(rawEvidenceJSON string) (int, bool) {
	if strings.TrimSpace(rawEvidenceJSON) == "" {
		return 0, false
	}
	var payload map[string]any
	if err := json.Unmarshal([]byte(rawEvidenceJSON), &payload); err != nil {
		return 0, false
	}
	value, ok := payload["domain_age_days"]
	if !ok {
		return 0, false
	}
	return coerceInt(value)
}

func coerceInt(value any) (int, bool) {
	switch v := value.(type) {
	case float64:
		return int(v), true
	case int:
		return v, true
	case int64:
		return int(v), true
	case string:
		if strings.TrimSpace(v) == "" {
			return 0, false
		}
		parsed, err := strconv.Atoi(strings.TrimSpace(v))
		if err != nil {
			return 0, false
		}
		return parsed, true
	default:
		return 0, false
	}
}
