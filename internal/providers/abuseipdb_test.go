package providers

import (
	"context"
	"os"
	"testing"

	"github.com/joho/godotenv"
)

func TestAbuseIPDBProviderCollect(t *testing.T) {
	_ = godotenv.Load("../../.env")

	apiKey := os.Getenv("ABUSEIPDB_API_KEY")
	if apiKey == "" {
		t.Skip("ABUSEIPDB_API_KEY not set. Skipping integration test.")
	}

	provider := NewAbuseIPDBProvider(apiKey)

	records, err := provider.Collect(context.Background())

	if err != nil {
		t.Fatalf("Collect returned an error: %v", err)
	}
	if len(records) == 0 {
		t.Fatal("expected at least one threat from abuseipdb collect")
	}
	record := records[0]

	if record.IOCType != "ip" {
		t.Errorf("Expected IOCType to be ip, got %s", record.IOCType)
	}

	if record.SourceName != "abuseipdb" {
		t.Errorf("Expected SourceName to be abuseipdb, got %s", record.SourceName)
	}
	if len(record.RawEvidence) == 0 {
		t.Error("Expected RawEvidence map to be populated")
	}
}
