package output

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"time"

	"github.com/Sahtattou/SPECTER/pkg/models"
)

type stixObject map[string]any

func ExportSTIX(records []models.ThreatRecord) (string, error) {
	ts := time.Now().UTC().Format("20060102_150405")
	dir := "artifacts/stix"
	if err := os.MkdirAll(dir, 0o755); err != nil {
		return "", err
	}
	outPath := filepath.Join(dir, fmt.Sprintf("specter_output_%s.stix.json", ts))

	objects := make([]stixObject, 0, len(records))
	for _, r := range records {
		pattern := toPattern(r.IOCType, r.IOCValue)
		conf := 0
		if r.CompositeScore != nil {
			conf = int(*r.CompositeScore)
		}
		objects = append(objects, stixObject{
			"type":         "indicator",
			"spec_version": "2.1",
			"id":           "indicator--" + r.EventID,
			"created":      r.CreatedAt.UTC().Format(time.RFC3339),
			"modified":     r.UpdatedAt.UTC().Format(time.RFC3339),
			"name":         r.IOCValue,
			"pattern_type": "stix",
			"pattern":      pattern,
			"confidence":   conf,
			"labels":       []string{r.ThreatLevel, "specter"},
			"external_references": []map[string]string{
				{"source_name": r.SourceName, "url": r.SourceURL},
			},
			"x_specter_days_to_attack":      r.DaysToAttack,
			"x_specter_corroboration_count": r.CorroborationCount,
			"x_specter_pipeline_stage":      r.PipelineStage,
		})
	}

	bundle := map[string]any{
		"type":    "bundle",
		"id":      "bundle--specter-" + ts,
		"objects": objects,
	}

	f, err := os.Create(outPath)
	if err != nil {
		return "", err
	}
	defer f.Close()

	enc := json.NewEncoder(f)
	enc.SetIndent("", "  ")
	if err := enc.Encode(bundle); err != nil {
		return "", err
	}

	return outPath, nil
}

func toPattern(iocType, value string) string {
	switch iocType {
	case "ip":
		return fmt.Sprintf("[ipv4-addr:value = '%s']", value)
	case "domain":
		return fmt.Sprintf("[domain-name:value = '%s']", value)
	case "url":
		return fmt.Sprintf("[url:value = '%s']", value)
	default:
		return fmt.Sprintf("[domain-name:value = '%s']", value)
	}
}
