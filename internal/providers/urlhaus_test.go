package providers

import (
	"os"
	"testing"

	"github.com/joho/godotenv"
)

func TestURLhausProviderFetch(t *testing.T) {
	_ = godotenv.Load("../../.env")

	apiKey := os.Getenv("URLHAUS_API_KEY")
	if apiKey == "" {
		t.Skip("Skipping URLhaus test: URLHAUS_API_KEY not set")
	}

	provider := InitURLhausProvider(apiKey)

	target := "example.com"

	record, err := provider.Fetch(target)

	if err != nil {
		t.Fatalf("Fetch returned an error: %v", err)
	}

	if record == nil {
		t.Fatal("Expected a ThreatRecord pointer, got nil")
	}

	if record.Target != target {
		t.Errorf("Expected Target to be %s, got %s", target, record.Target)
	}

	if record.Source != "URLhaus" {
		t.Errorf("Expected Source to be URLhaus, got %s", record.Source)
	}
}
