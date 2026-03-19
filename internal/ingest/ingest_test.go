package ingest

import (
	"testing"

	"github.com/Sahtattou/SPECTER/pkg/models"
)

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

func TestDedupeHashStableAndDistinct(t *testing.T) {
	recA := models.ThreatRecord{IOCType: "ip", IOCValue: "8.8.8.8", SourceName: "shodan"}
	recASameCaseVariant := models.ThreatRecord{IOCType: "IP", IOCValue: "8.8.8.8", SourceName: "SHODAN"}
	recB := models.ThreatRecord{IOCType: "ip", IOCValue: "8.8.8.8", SourceName: "abuseipdb"}

	hA := DedupeHash(recA)
	hA2 := DedupeHash(recASameCaseVariant)
	hB := DedupeHash(recB)

	if hA == "" {
		t.Fatal("expected non-empty hash")
	}
	if hA != hA2 {
		t.Fatalf("expected case-insensitive stable hash equality, got %q != %q", hA, hA2)
	}
	if hA == hB {
		t.Fatalf("expected different source to produce distinct hash, got same hash %q", hA)
	}
}
