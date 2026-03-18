package providers

import (
	"context"
	"os"
	"testing"
)

func TestOTXProvider_Collect(t *testing.T) {
	apiKey := os.Getenv("OTX_API_KEY")
	if apiKey == "" {
		t.Skip("Skipping OTX test: OTX_API_KEY not set")
	}

	provider := NewOTXProvider(apiKey)
	records, err := provider.Collect(context.Background())

	if err != nil {
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
