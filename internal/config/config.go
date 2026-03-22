package config

import (
	"os"
	"strconv"
	"strings"

	"github.com/joho/godotenv"
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

	ShodanTargets       []string
	AbuseIPDBTargets    []string
	OTXTargets          []string
	URLHausHosts        []string
	CRTShQuery          string
	CRTShDeduplicate    bool
	CRTShExcludeExpired bool
	CRTShMaxResults     int
}

func Load() Config {
	_ = godotenv.Load()

	demoMode := envBool("DEMO_MODE", false)

	cfg := Config{
		APIPort:                   env("API_PORT", "8080"),
		WorkerConcurrency:         envInt("WORKER_CONCURRENCY", 4),
		CollectionIntervalSeconds: envInt("COLLECTION_INTERVAL_SECONDS", 60),
		DBDSN:                     env("DB_DSN", "file:specter.db?_busy_timeout=5000&_journal_mode=WAL"),
		AbuseIPDBAPIKey:           os.Getenv("ABUSEIPDB_API_KEY"),
		OTXAPIKey:                 os.Getenv("OTX_API_KEY"),
		ShodanAPIKey:              os.Getenv("SHODAN_API_KEY"),
		URLHausAPIKey:             os.Getenv("URLHAUS_API_KEY"),
		LogLevel:                  env("LOG_LEVEL", "INFO"),
		DemoMode:                  demoMode,
		ShodanTargets:             envCSV("SHODAN_TARGETS"),
		AbuseIPDBTargets:          envCSV("ABUSEIPDB_TARGETS"),
		OTXTargets:                envCSV("OTX_TARGETS"),
		URLHausHosts:              envCSV("URLHAUS_HOSTS"),
		CRTShQuery:                strings.TrimSpace(os.Getenv("CRTSH_QUERY")),
		CRTShDeduplicate:          envBool("CRTSH_DEDUPLICATE", true),
		CRTShExcludeExpired:       envBool("CRTSH_EXCLUDE_EXPIRED", true),
		CRTShMaxResults:           envInt("CRTSH_MAX_RESULTS", 1000),
	}

	return cfg
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

func envCSV(k string) []string {
	v := strings.TrimSpace(os.Getenv(k))
	if v == "" {
		return nil
	}
	parts := strings.Split(v, ",")
	out := make([]string, 0, len(parts))
	for _, p := range parts {
		t := strings.TrimSpace(p)
		if t != "" {
			out = append(out, t)
		}
	}
	return out
}
