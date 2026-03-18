package main

import (
	"context"
	"fmt"
	"log"
	"sync"
	"time"

	"github.com/Sahtattou/SPECTER/internal/config"
	"github.com/Sahtattou/SPECTER/internal/ingest"
	"github.com/Sahtattou/SPECTER/internal/providers"
	"github.com/Sahtattou/SPECTER/internal/scoring"
	"github.com/Sahtattou/SPECTER/internal/storage"
	"github.com/Sahtattou/SPECTER/internal/validation"
)

func main() {
	cfg := config.Load()

	repo, err := storage.NewSQLiteRepository(cfg.DBDSN)
	if err != nil {
		log.Fatalf("init repository: %v", err)
	}
	defer repo.Close()

	providerList := []providers.Provider{
		providers.NewCRTShProvider(),
		providers.NewShodanProvider(cfg.ShodanAPIKey),
		providers.NewURLHausProvider(cfg.URLHausAPIKey),
		providers.NewAbuseIPDBProvider(cfg.AbuseIPDBAPIKey),
		providers.NewOTXProvider(cfg.OTXAPIKey),
	}

	interval := time.Duration(cfg.CollectionIntervalSeconds) * time.Second
	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	log.Printf("collector started interval=%s providers=%d", interval, len(providerList))

	collectAll := func() {
		ctx, cancel := context.WithTimeout(context.Background(), 90*time.Second)
		defer cancel()

		// Buffered channel prevents goroutine blocking on send.
		results := make(chan string, len(providerList))

		var wg sync.WaitGroup
		wg.Add(len(providerList))

		for _, p := range providerList {
			p := p // capture
			go func() {
				defer wg.Done()

				start := time.Now()
				threats, err := p.Collect(ctx)
				if err != nil {
					results <- p.Name() + " error: " + err.Error()
					return
				}

				success := 0
				for _, t := range threats {
					rec, err := ingest.NormalizeThreat(t)
					if err != nil {
						continue
					}
					rec = validation.Detect(rec)
					rec = scoring.Score(rec)
					rec.UpdatedAt = time.Now().UTC()
					if err := repo.UpsertRecord(ctx, rec); err != nil {
						continue
					}
					success++
				}

				results <- p.Name() + " collected=" + itoa(len(threats)) +
					" persisted=" + itoa(success) +
					" elapsed=" + time.Since(start).String()
			}()
		}

		// Close results after all workers complete.
		go func() {
			wg.Wait()
			close(results)
		}()

		for msg := range results {
			log.Printf("[collector] %s", msg)
		}
	}

	collectAll() // initial immediate run
	for range ticker.C {
		collectAll()
	}
}

func itoa(v int) string {
	return fmt.Sprintf("%d", v)
}
