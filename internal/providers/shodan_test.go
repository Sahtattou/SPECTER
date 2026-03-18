package providers

import (
	"os"
	"testing"

	"github.com/joho/godotenv"
)

func TestShodanProviderFetch(t *testing.T) {
	_ = godotenv.Load("../../.env")

	apiKey := os.Getenv("SHODAN_API_KEY")
	if apiKey == "" {
		t.Skip("SHODAN_API_KEY not set. Skipping integration test.")
	}

	provider := InitShodanProvider(apiKey)

	targetIP := "8.8.8.8"
	record, err := provider.Fetch(targetIP)

	if err != nil {
		t.Fatalf("Shodan Fetch returned an error: %v", err)
	}

	if record.Target != targetIP {
		t.Errorf("Expected Target to be %s, got %s", targetIP, record.Target)
	}

	if record.Source != "shodan" {
		t.Errorf("Expected Source to be Shodan, got %s", record.Source)
	}

	if len(record.Details) == 0 {
		t.Error("Expected Details map to contain data, but it was empty")
	}
}
