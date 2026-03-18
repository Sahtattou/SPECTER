package providers

import (
	"context"
	"strings"
	"testing"
)

func TestCrtShProviderCollect(t *testing.T) {
	provider := NewCRTShProvider()

	records, err := provider.Collect(context.Background())

	if err != nil {
		if strings.Contains(err.Error(), "503") || strings.Contains(strings.ToLower(err.Error()), "service unavailable") {
			t.Skipf("Skipping crt.sh integration test due to remote outage: %v", err)
		}
		t.Fatalf("Collect returned an error: %v", err)
	}
	if len(records) == 0 {
		t.Fatal("expected at least one threat from crtsh collect")
	}
	record := records[0]

	if record.IOCType != "domain" {
		t.Errorf("Expected IOCType domain, got %s", record.IOCType)
	}

	if record.SourceName != "crt.sh" {
		t.Errorf("Expected SourceName to be crt.sh, got %s", record.SourceName)
	}

	if len(record.RawEvidence) == 0 {
		t.Error("Expected raw evidence to be populated")
	}
}
