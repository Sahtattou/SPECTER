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

	providerList := make([]providers.Provider, 0, 5)

	if cfg.CRTShQuery != "" {
		providerList = append(providerList, providers.NewCRTShProvider(
			cfg.CRTShQuery,
			cfg.CRTShDeduplicate,
			cfg.CRTShExcludeExpired,
			cfg.CRTShMaxResults,
		))
	}

	if len(cfg.ShodanTargets) > 0 {
		if cfg.ShodanAPIKey == "" {
			log.Printf("collector skipping shodan: SHODAN_TARGETS set but SHODAN_API_KEY is empty")
		} else {
			providerList = append(providerList, providers.NewShodanProvider(cfg.ShodanAPIKey, cfg.ShodanTargets))
		}
	}
	if len(cfg.URLHausHosts) > 0 {
		if cfg.URLHausAPIKey == "" {
			log.Printf("collector skipping urlhaus: URLHAUS_HOSTS set but URLHAUS_API_KEY is empty")
		} else {
			providerList = append(providerList, providers.NewURLHausProvider(cfg.URLHausAPIKey, cfg.URLHausHosts))
		}
	}
	if len(cfg.AbuseIPDBTargets) > 0 {
		if cfg.AbuseIPDBAPIKey == "" {
			log.Printf("collector skipping abuseipdb: ABUSEIPDB_TARGETS set but ABUSEIPDB_API_KEY is empty")
		} else {
			providerList = append(providerList, providers.NewAbuseIPDBProvider(cfg.AbuseIPDBAPIKey, cfg.AbuseIPDBTargets))
		}
	}
	if len(cfg.OTXTargets) > 0 {
		if cfg.OTXAPIKey == "" {
			log.Printf("collector skipping otx: OTX_TARGETS set but OTX_API_KEY is empty")
		} else {
			providerList = append(providerList, providers.NewOTXProvider(cfg.OTXAPIKey, cfg.OTXTargets))
		}
	}

	if len(providerList) == 0 {
		log.Printf("collector warning: no providers configured; set SHODAN_TARGETS, ABUSEIPDB_TARGETS, OTX_TARGETS, URLHAUS_HOSTS, or CRTSH_QUERY")
	}

	interval := time.Duration(cfg.CollectionIntervalSeconds) * time.Second
	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	activeProviders := make([]string, 0, len(providerList))
	for _, p := range providerList {
		activeProviders = append(activeProviders, p.Name())
	}
	log.Printf(
		"collector started interval=%s providers=%d active=%v targets={shodan:%d abuseipdb:%d otx:%d urlhaus:%d crtsh:%t}",
		interval,
		len(providerList),
		activeProviders,
		len(cfg.ShodanTargets),
		len(cfg.AbuseIPDBTargets),
		len(cfg.OTXTargets),
		len(cfg.URLHausHosts),
		cfg.CRTShQuery != "",
	)

	collectAll := func() {
		ctx, cancel := context.WithTimeout(context.Background(), 90*time.Second)
		defer cancel()

		seenHashes := make(map[string]struct{})
		var seenMu sync.Mutex

		// Buffered channel prevents goroutine blocking on send.
		results := make(chan string, len(providerList))

		var wg sync.WaitGroup
		wg.Add(len(providerList))

		for _, p := range providerList {
			go func() {
				defer wg.Done()

				start := time.Now()
				threats, err := p.Collect(ctx)
				if err != nil {
					results <- p.Name() + " error: " + err.Error()
					return
				}

				success := 0
				skippedDuplicates := 0
				for _, t := range threats {
					rec, err := ingest.NormalizeThreat(t)
					if err != nil {
						continue
					}

					h := ingest.DedupeHash(rec)
					seenMu.Lock()
					_, exists := seenHashes[h]
					if !exists {
						seenHashes[h] = struct{}{}
					}
					seenMu.Unlock()
					if exists {
						skippedDuplicates++
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
					" dedup_skipped=" + itoa(skippedDuplicates) +
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
