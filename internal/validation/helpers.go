package validation

import (
	"time"

	"github.com/Sahtattou/SPECTER/pkg/models"
)

func DetectPoison() models.ThreatRecord {
	now := time.Now().UTC()
	rec := models.ThreatRecord{
		EventID:            "detect-poison-scaffold",
		IOCValue:           "example.com",
		IOCType:            "domain",
		SourceName:         "scaffold",
		RawEvidenceJSON:    "{}",
		CollectedAt:        now,
		CorroborationCount: 1,
		CreatedAt:          now,
		UpdatedAt:          now,
	}
	return Detect(rec)
}
