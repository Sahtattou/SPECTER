package ingest

import "testing"

func TestIngestScaffold(t *testing.T) {
	if got := DetectType("1.2.3.4"); got != "ip" {
		t.Fatalf("expected ip, got %s", got)
	}
	if got := DetectType("https://example.com"); got != "url" {
		t.Fatalf("expected url, got %s", got)
	}
	if got := DetectType("example.com"); got != "domain" {
		t.Fatalf("expected domain, got %s", got)
	}

	BuildDedupeHash()
}
