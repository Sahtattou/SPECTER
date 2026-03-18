package ingest

import (
	"encoding/json"
	"net"
	"strings"
	"time"

	"github.com/Sahtattou/SPECTER/pkg/models"
	"github.com/google/uuid"
)

func DetectType(target string) string {
	if net.ParseIP(target) != nil {
		return "ip"
	}
	if strings.HasPrefix(target, "http") {
		return "url"
	}
	return "domain"
}

func BuildEnvelope(target string, rawResults map[string]*models.ThreatRecord) (*models.IOCEnvelope, error) {
	evidenceBytes, err := json.Marshal(rawResults)
	if err != nil {
		return nil, err
	}

	env := &models.IOCEnvelope{
		IOCUUID:            uuid.New().String(),
		RawValue:           target,
		IOCType:            DetectType(target),
		SourceName:         "SPECTER_GO_ENGINE",
		SourceQuery:        target,
		RawEvidence:        string(evidenceBytes),
		CollectedAt:        time.Now().UTC(),
		PipelineStage:      "raw_ingest",
		IsSynthetic:        false,
		CorroborationCount: len(rawResults),
	}

	return env, nil
}
