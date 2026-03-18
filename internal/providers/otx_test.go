package providers

import (
	"os"
	"testing"
)

func TestOTXProvider_Fetch(t *testing.T) {
	apiKey := os.Getenv("OTX_API_KEY")
	if apiKey == "" {
		t.Skip("Skipping OTX test: OTX_API_KEY not set")
	}

	provider := InitOTXProvider(apiKey)
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

	if record.Source != "AlienVault OTX" {
		t.Errorf("Expected Source to be AlienVault OTX, got %s", record.Source)
	}
}
