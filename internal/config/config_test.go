package config

import "testing"

func TestConfigScaffold(t *testing.T) {
	cfg := Config{}
	if cfg.APIPort != "" {
		t.Fatalf("expected default scaffold to be empty")
	}
}
