package output

import (
	"fmt"
	"os"
	"path/filepath"
	"time"

	"github.com/Sahtattou/SPECTER/pkg/models"
)

// Minimal text report placeholder (named .pdf by convention in plan).
func ExportReport(records []models.ThreatRecord) (string, error) {
	ts := time.Now().UTC().Format("20060102_150405")
	dir := "artifacts/reports"
	if err := os.MkdirAll(dir, 0o755); err != nil {
		return "", err
	}
	outPath := filepath.Join(dir, fmt.Sprintf("specter_report_%s.pdf", ts))

	f, err := os.Create(outPath)
	if err != nil {
		return "", err
	}
	defer f.Close()

	_, _ = fmt.Fprintln(f, "SPECTER Threat Report")
	_, _ = fmt.Fprintln(f, "----------------------")
	_, _ = fmt.Fprintf(f, "Generated at: %s\n\n", time.Now().UTC().Format(time.RFC3339))
	_, _ = fmt.Fprintf(f, "Total records: %d\n\n", len(records))

	for i, r := range records {
		score := 0.0
		if r.CompositeScore != nil {
			score = *r.CompositeScore
		}
		_, _ = fmt.Fprintf(f, "%d) %s (%s)\n", i+1, r.IOCValue, r.IOCType)
		_, _ = fmt.Fprintf(f, "   Source: %s\n", r.SourceName)
		_, _ = fmt.Fprintf(f, "   Stage: %s | Level: %s | Score: %.2f | ETA: %s\n\n",
			r.PipelineStage, r.ThreatLevel, score, r.DaysToAttack)
	}

	return outPath, nil
}
