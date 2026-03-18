package config

// Config holds runtime settings for Go services.
type Config struct {
APIPort                   string
WorkerConcurrency         int
CollectionIntervalSeconds int
DBDSN                     string
}
