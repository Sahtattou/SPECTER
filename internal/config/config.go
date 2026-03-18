package config

import (
	"os"
	"strconv"
)

type Config struct {
	APIPort                   string
	WorkerConcurrency         int
	CollectionIntervalSeconds int
	DBDSN                     string

	AbuseIPDBAPIKey string
	OTXAPIKey       string
	ShodanAPIKey    string
	URLHausAPIKey   string

	LogLevel string
	DemoMode bool
}

func Load() Config {
	return Config{
		APIPort:                   env("API_PORT", "8080"),
		WorkerConcurrency:         envInt("WORKER_CONCURRENCY", 4),
		CollectionIntervalSeconds: envInt("COLLECTION_INTERVAL_SECONDS", 60),
		DBDSN:                     env("DB_DSN", "file:specter.db?_busy_timeout=5000&_journal_mode=WAL"),
		AbuseIPDBAPIKey:           os.Getenv("ABUSEIPDB_API_KEY"),
		OTXAPIKey:                 os.Getenv("OTX_API_KEY"),
		ShodanAPIKey:              os.Getenv("SHODAN_API_KEY"),
		URLHausAPIKey:             os.Getenv("URLHAUS_API_KEY"),
		LogLevel:                  env("LOG_LEVEL", "INFO"),
		DemoMode:                  envBool("DEMO_MODE", true),
	}
}

func env(k, def string) string {
	v := os.Getenv(k)
	if v == "" {
		return def
	}
	return v
}

func envInt(k string, def int) int {
	v := os.Getenv(k)
	if v == "" {
		return def
	}
	i, err := strconv.Atoi(v)
	if err != nil {
		return def
	}
	return i
}

func envBool(k string, def bool) bool {
	v := os.Getenv(k)
	if v == "" {
		return def
	}
	b, err := strconv.ParseBool(v)
	if err != nil {
		return def
	}
	return b
}
