package scoring

import "github.com/Sahtattou/SPECTER/pkg/models"

func Score(rec models.ThreatRecord) models.ThreatRecord {
	if rec.PipelineStage == "quarantined" {
		return rec
	}

	score := 20.0
	score += float64(rec.CorroborationCount * 10)

	if rec.IsSynthetic {
		score -= 40
	}
	for _, p := range rec.OpenPorts {
		if p == 50050 || p == 40056 || p == 8888 {
			score += 20
			break
		}
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
	rec.PipelineStage = "scored"
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
