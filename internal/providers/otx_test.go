package providers

import (
	"context"
	"os"
	"strings"
	"testing"
)

func TestOTXProvider_Collect(t *testing.T) {
	apiKey := os.Getenv("OTX_API_KEY")
	if apiKey == "" {
		t.Skip("Skipping OTX test: OTX_API_KEY not set")
	}

	provider := NewOTXProvider(apiKey, []string{"8.8.8.8", "example.com"})
	records, err := provider.Collect(context.Background())

	if err != nil {
		lower := strings.ToLower(err.Error())
		if strings.Contains(lower, "deadline") || strings.Contains(lower, "timeout") || strings.Contains(lower, "service unavailable") || strings.Contains(lower, "too many requests") {
			t.Skipf("Skipping OTX integration test due to transient upstream/network issue: %v", err)
		}
		t.Fatalf("Collect returned an error: %v", err)
	}
	if len(records) == 0 {
		t.Fatal("expected at least one threat from otx collect")
	}
	record := records[0]

	if record.SourceName != "otx" {
		t.Errorf("Expected SourceName to be otx, got %s", record.SourceName)
	}

	if record.IOCType == "" {
		t.Error("Expected IOCType to be set")
	}
}
