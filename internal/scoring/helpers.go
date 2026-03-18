package scoring

import (
	"time"

	"github.com/Sahtattou/SPECTER/pkg/models"
)

func ScoreThreat() models.ThreatRecord {
	now := time.Now().UTC()
	rec := models.ThreatRecord{
		EventID:            "score-threat-scaffold",
		IOCValue:           "example.com",
		IOCType:            "domain",
		SourceName:         "scaffold",
		RawEvidenceJSON:    "{}",
		CollectedAt:        now,
		CorroborationCount: 1,
		CreatedAt:          now,
		UpdatedAt:          now,
		PipelineStage:      "validated",
	}
	return Score(rec)
}
