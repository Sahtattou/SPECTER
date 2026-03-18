package providers

import (
	"os"
	"testing"

	"github.com/joho/godotenv"
)

func TestAbuseIPDBProviderFetch(t *testing.T) {
	_ = godotenv.Load("../../.env")

	apiKey := os.Getenv("ABUSEIPDB_API_KEY")
	if apiKey == "" {
		t.Skip("ABUSEIPDB_API_KEY not set. Skipping integration test.")
	}

	provider := InitAbuseIPDBProvider(apiKey)

	targetIP := "8.8.8.8"
	record, err := provider.Fetch(targetIP)

	if err != nil {
		t.Fatalf("Fetch returned an error: %v", err)
	}

	if record == nil {
		t.Fatal("Expected a ThreatRecord, got nil")
	}

	if record.Target != targetIP {
		t.Errorf("Expected Target to be %s, got %s", targetIP, record.Target)
	}

	if record.Source != "AbuseIPDB" {
		t.Errorf("Expected Source to be AbuseIPDB, got %s", record.Source)
	}

	if record.IsMalicious {
		t.Errorf("Expected 8.8.8.8 to NOT be malicious")
	}
}
