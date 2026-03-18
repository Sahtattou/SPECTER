package ingest

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"strings"
	"time"

	"github.com/Sahtattou/SPECTER/pkg/models"
)

func normalizeIOCType(v string) string {
	s := strings.ToLower(strings.TrimSpace(v))
	switch s {
	case "ipv4", "ipv6":
		return "ip"
	case "domain-name":
		return "domain"
	default:
		return s
	}
}

func stableID(parts ...string) string {
	key := strings.ToLower(strings.Join(parts, "|"))
	sum := sha256.Sum256([]byte(key))
	return hex.EncodeToString(sum[:16])
}

func NormalizeThreat(t models.Threat) (models.ThreatRecord, error) {
	raw, err := json.Marshal(t.RawEvidence)
	if err != nil {
		return models.ThreatRecord{}, fmt.Errorf("marshal raw evidence: %w", err)
	}

	now := time.Now().UTC()
	rec := models.ThreatRecord{
		EventID:            stableID(t.SourceName, normalizeIOCType(t.IOCType), t.IOCValue),
		IOCValue:           strings.TrimSpace(t.IOCValue),
		IOCType:            normalizeIOCType(t.IOCType),
		SourceName:         strings.TrimSpace(t.SourceName),
		SourceURL:          strings.TrimSpace(t.SourceURL),
		SourceQuery:        strings.TrimSpace(t.SourceQuery),
		RawEvidenceJSON:    string(raw),
		CollectedAt:        t.CollectedAt.UTC(),
		CorroborationCount: t.Corroboration,
		OpenPorts:          t.OpenPorts,
		ASN:                t.ASN,
		IsSynthetic:        t.IsSynthetic,
		PoisonAttackType:   t.PoisonAttackType,
		PipelineStage:      "ingested",
		CreatedAt:          now,
		UpdatedAt:          now,
	}
	return rec, nil
}
