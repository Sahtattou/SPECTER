package providers

import (
	"context"
	"os"
	"testing"

	"github.com/joho/godotenv"
)

func TestURLhausProviderCollect(t *testing.T) {
	_ = godotenv.Load("../../.env")

	apiKey := os.Getenv("URLHAUS_API_KEY")
	if apiKey == "" {
		t.Skip("Skipping URLhaus test: URLHAUS_API_KEY not set")
	}

	provider := NewURLHausProvider(apiKey)

	records, err := provider.Collect(context.Background())

	if err != nil {
		t.Fatalf("Collect returned an error: %v", err)
	}
	if len(records) == 0 {
		t.Fatal("expected at least one threat from urlhaus collect")
	}
	record := records[0]

	if record.IOCType != "domain" {
		t.Errorf("Expected IOCType to be domain, got %s", record.IOCType)
	}

	if record.SourceName != "urlhaus" {
		t.Errorf("Expected SourceName to be urlhaus, got %s", record.SourceName)
	}
}
