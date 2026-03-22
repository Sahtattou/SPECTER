package output

import (
	"bytes"
	"os"
	"strings"
	"testing"
	"time"

	"github.com/Sahtattou/SPECTER/pkg/models"
)

func TestExportReport_WritesValidPDFFile(t *testing.T) {
	now := time.Now().UTC()
	records := []models.ThreatRecord{
		{
			IOCValue:           "example.com",
			IOCType:            "domain",
			SourceName:         "otx",
			PipelineStage:      "scored",
			ThreatLevel:        "high",
			DaysToAttack:       "3-7",
			CorroborationCount: 3,
			CreatedAt:          now,
			UpdatedAt:          now,
		},
	}

	path, err := ExportReport(records)
	if err != nil {
		t.Fatalf("export report failed: %v", err)
	}
	defer os.Remove(path)

	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("failed to read generated report: %v", err)
	}

	if !bytes.HasPrefix(data, []byte("%PDF-1.4")) {
		headerLen := min(len(data), 16)
		t.Fatalf("expected PDF header, got %q", string(data[:headerLen]))
	}

	if !strings.Contains(string(data), "%%EOF") {
		t.Fatalf("expected PDF EOF marker")
	}
}
