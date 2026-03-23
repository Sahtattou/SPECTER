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

func TestLoadProviderEnableFlagsDefaultTrue(t *testing.T) {
	t.Setenv("ENABLE_SHODAN", "")
	t.Setenv("ENABLE_ABUSEIPDB", "")
	t.Setenv("ENABLE_OTX", "")
	t.Setenv("ENABLE_URLHAUS", "")
	t.Setenv("ENABLE_CRTSH", "")

	cfg := Load()

	if !cfg.EnableShodan || !cfg.EnableAbuseIPDB || !cfg.EnableOTX || !cfg.EnableURLHaus || !cfg.EnableCRTSh {
		t.Fatalf("expected all provider enable flags to default true")
	}
}

func TestLoadProviderEnableFlagsFromEnv(t *testing.T) {
	t.Setenv("ENABLE_SHODAN", "false")
	t.Setenv("ENABLE_ABUSEIPDB", "false")
	t.Setenv("ENABLE_OTX", "false")
	t.Setenv("ENABLE_URLHAUS", "false")
	t.Setenv("ENABLE_CRTSH", "false")

	cfg := Load()

	if cfg.EnableShodan || cfg.EnableAbuseIPDB || cfg.EnableOTX || cfg.EnableURLHaus || cfg.EnableCRTSh {
		t.Fatalf("expected all provider enable flags to load false from env")
	}
}
