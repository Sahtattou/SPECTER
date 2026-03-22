package config

import (
	"testing"
)

func TestLoadDefaultsForProductionMode(t *testing.T) {
	t.Setenv("DEMO_MODE", "false")
	t.Setenv("SHODAN_TARGETS", "")
	t.Setenv("ABUSEIPDB_TARGETS", "")
	t.Setenv("OTX_TARGETS", "")
	t.Setenv("URLHAUS_HOSTS", "")
	t.Setenv("CRTSH_QUERY", "")

	cfg := Load()

	if cfg.DemoMode {
		t.Fatalf("expected DemoMode=false")
	}
	if len(cfg.ShodanTargets) != 0 || len(cfg.AbuseIPDBTargets) != 0 || len(cfg.OTXTargets) != 0 || len(cfg.URLHausHosts) != 0 {
		t.Fatalf("expected no default provider targets when demo mode is disabled")
	}
	if cfg.CRTShQuery != "" {
		t.Fatalf("expected empty CRTShQuery when demo mode is disabled")
	}
}

func TestLoadDefaultsForDemoMode(t *testing.T) {
	t.Setenv("DEMO_MODE", "true")
	t.Setenv("SHODAN_TARGETS", "")
	t.Setenv("ABUSEIPDB_TARGETS", "")
	t.Setenv("OTX_TARGETS", "")
	t.Setenv("URLHAUS_HOSTS", "")
	t.Setenv("CRTSH_QUERY", "")

	cfg := Load()

	if !cfg.DemoMode {
		t.Fatalf("expected DemoMode=true")
	}
	if len(cfg.ShodanTargets) != 0 || len(cfg.AbuseIPDBTargets) != 0 || len(cfg.OTXTargets) != 0 || len(cfg.URLHausHosts) != 0 {
		t.Fatalf("expected no implicit provider targets in demo mode")
	}
	if cfg.CRTShQuery != "" {
		t.Fatalf("expected no implicit CRTShQuery in demo mode")
	}
}
