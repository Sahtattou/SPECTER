package providers

import (
	"context"
	"os"
	"strings"
	"testing"

	"github.com/joho/godotenv"
)

func TestShodanProviderCollect(t *testing.T) {
	_ = godotenv.Load("../../.env")

	apiKey := os.Getenv("SHODAN_API_KEY")
	if apiKey == "" {
		t.Skip("SHODAN_API_KEY not set. Skipping integration test.")
	}

	provider := NewShodanProvider(apiKey, []string{"8.8.8.8"})

	records, err := provider.Collect(context.Background())

	if err != nil {
		lower := strings.ToLower(err.Error())
		if strings.Contains(lower, "deadline") || strings.Contains(lower, "timeout") || strings.Contains(lower, "connection reset") || strings.Contains(lower, "service unavailable") || strings.Contains(lower, "too many requests") {
			t.Skipf("Skipping shodan integration test due to transient upstream/network issue: %v", err)
		}
		t.Fatalf("Shodan Collect returned an error: %v", err)
	}

	if len(records) == 0 {
		t.Fatal("expected at least one threat from shodan collect")
	}
	record := records[0]

	if record.SourceName != "shodan" {
		t.Errorf("Expected SourceName to be shodan, got %s", record.SourceName)
	}

	if len(record.RawEvidence) == 0 {
		t.Error("Expected RawEvidence map to contain data, but it was empty")
	}
}
