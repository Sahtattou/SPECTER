package scoring

import "github.com/Sahtattou/SPECTER/pkg/models"

const (
	penaltyPoisonDetected        = 100.0
	penaltySuspiciousTimestamp   = 35.0
	penaltyTTPBannerMismatch     = 45.0
	bonusHighRiskPortPrimary     = 20.0
	bonusHighRiskPortSecondary   = 8.0
	bonusCorroborationMultiplier = 10.0
)

var highRiskPrimaryPorts = map[int]struct{}{
	50050: {},
	40056: {},
	8888:  {},
	4444:  {},
}

var highRiskSecondaryPorts = map[int]struct{}{
	22:   {},
	3389: {},
	8080: {},
}

func Score(rec models.ThreatRecord) models.ThreatRecord {
	if rec.PipelineStage == "quarantined" {
		return rec
	}

	score := 20.0
	score += float64(rec.CorroborationCount) * bonusCorroborationMultiplier

	if rec.IsSynthetic {
		score -= 40
	}

	if rec.PoisonDetected != nil && *rec.PoisonDetected {
		score -= penaltyPoisonDetected
	}

	switch rec.DetectionRule {
	case "SUSPICIOUS_TIMESTAMP":
		score -= penaltySuspiciousTimestamp
	case "TTP_BANNER_MISMATCH":
		score -= penaltyTTPBannerMismatch
	}

	primaryMatched := false
	for _, p := range rec.OpenPorts {
		if _, ok := highRiskPrimaryPorts[p]; ok {
			score += bonusHighRiskPortPrimary
			primaryMatched = true
			continue
		}
		if _, ok := highRiskSecondaryPorts[p]; ok {
			score += bonusHighRiskPortSecondary
		}
	}
	if primaryMatched {
		score += 3
	}

	if score < 0 {
		score = 0
	}
	if score > 100 {
		score = 100
	}

	rec.CompositeScore = &score
	rec.ThreatLevel = mapLevel(score)
	rec.DaysToAttack = mapDays(score)
	if rec.PoisonDetected != nil && *rec.PoisonDetected {
		rec.PipelineStage = "quarantined"
	} else {
		rec.PipelineStage = "scored"
	}
	return rec
}

func mapLevel(score float64) string {
	switch {
	case score >= 80:
		return "critical"
	case score >= 60:
		return "high"
	case score >= 40:
		return "medium"
	default:
		return "low"
	}
}

func mapDays(score float64) string {
	switch {
	case score >= 80:
		return "0-2"
	case score >= 60:
		return "3-7"
	default:
		return "8+"
	}
}
