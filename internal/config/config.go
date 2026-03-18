package config

import (
	"log"
	"os"
	"strconv"
	"strings"

	"github.com/joho/godotenv"
)

type Config struct {
	AbuseIPDBKey string
	OTXKey       string
	ShodanKey    string

	APIPort                   string
	WorkerConcurrency         int
	CollectionIntervalSeconds int
	DBDSN                     string

	LogLevel string
	DemoMode bool
}

func LoadConfig() *Config {
	if err := godotenv.Load(); err != nil {
		log.Println("[!] No .env file found, relying on system environment variables.")
	}

	return &Config{
		AbuseIPDBKey: getEnv("ABUSEIPDB_API_KEY", ""),
		OTXKey:       getEnv("OTX_API_KEY", ""),
		ShodanKey:    getEnv("SHODAN_API_KEY", ""),

		APIPort:                   getEnv("API_PORT", "8080"),
		WorkerConcurrency:         getEnvAsInt("WORKER_CONCURRENCY", 4),
		CollectionIntervalSeconds: getEnvAsInt("COLLECTION_INTERVAL_SECONDS", 60),
		DBDSN:                     getEnv("DB_DSN", "./specter_intelligence.db"),

		LogLevel: getEnv("LOG_LEVEL", "INFO"),
		DemoMode: getEnvAsBool("DEMO_MODE", true),
	}
}

func getEnv(key, fallback string) string {
	if value, exists := os.LookupEnv(key); exists {
		return value
	}
	return fallback
}

func getEnvAsInt(key string, fallback int) int {
	valueStr := getEnv(key, "")
	if value, err := strconv.Atoi(valueStr); err == nil {
		return value
	}
	return fallback
}

func getEnvAsBool(key string, fallback bool) bool {
	valueStr := getEnv(key, "")
	if value, err := strconv.ParseBool(strings.ToLower(valueStr)); err == nil {
		return value
	}
	return fallback
}
