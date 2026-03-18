package providers

import (
	"testing"
)

func TestCrtShProvider_Fetch(t *testing.T) {
	provider := InitCrtShProvider()

	targetDomain := "scanme.nmap.org"

	record, err := provider.Fetch(targetDomain)

	if err != nil {
		t.Fatalf("Fetch returned an error: %v", err)
	}

	if record.Target != targetDomain {
		t.Errorf("Expected Target to be %s, got %s", targetDomain, record.Target)
	}

	if record.Source != "crt.sh" {
		t.Errorf("Expected Source to be crt.sh, got %s", record.Source)
	}

	if count, ok := record.Details["subdomain_count"].(int); !ok || count == 0 {
		t.Error("Expected to find subdomains, but got 0 or invalid type")
	}
}
