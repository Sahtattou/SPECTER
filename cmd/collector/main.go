package main

import (
	"context"
	"errors"
	"fmt"
	"log"
	"strings"
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

	type providerState struct {
		name                string
		provider            providers.Provider
		consecutiveFailures int
		disabledUntil       time.Time
		disabledReason      string
	}

	if cfg.EnableCRTSh && cfg.CRTShQuery != "" {
		providerList = append(providerList, providers.NewCRTShProvider(
			cfg.CRTShQuery,
			cfg.CRTShDeduplicate,
			cfg.CRTShExcludeExpired,
			cfg.CRTShMaxResults,
		))
	} else if !cfg.EnableCRTSh {
		log.Printf("collector skipping crt.sh: ENABLE_CRTSH=false")
	}

	if !cfg.EnableShodan {
		log.Printf("collector skipping shodan: ENABLE_SHODAN=false")
	} else if len(cfg.ShodanTargets) > 0 {
		if cfg.ShodanAPIKey == "" {
			log.Printf("collector skipping shodan: SHODAN_TARGETS set but SHODAN_API_KEY is empty")
		} else {
			providerList = append(providerList, providers.NewShodanProvider(cfg.ShodanAPIKey, cfg.ShodanTargets))
		}
	}
	if !cfg.EnableURLHaus {
		log.Printf("collector skipping urlhaus: ENABLE_URLHAUS=false")
	} else if len(cfg.URLHausHosts) > 0 {
		if cfg.URLHausAPIKey == "" {
			log.Printf("collector skipping urlhaus: URLHAUS_HOSTS set but URLHAUS_API_KEY is empty")
		} else {
			providerList = append(providerList, providers.NewURLHausProvider(cfg.URLHausAPIKey, cfg.URLHausHosts))
		}
	}
	if !cfg.EnableAbuseIPDB {
		log.Printf("collector skipping abuseipdb: ENABLE_ABUSEIPDB=false")
	} else if len(cfg.AbuseIPDBTargets) > 0 {
		if cfg.AbuseIPDBAPIKey == "" {
			log.Printf("collector skipping abuseipdb: ABUSEIPDB_TARGETS set but ABUSEIPDB_API_KEY is empty")
		} else {
			providerList = append(providerList, providers.NewAbuseIPDBProvider(cfg.AbuseIPDBAPIKey, cfg.AbuseIPDBTargets))
		}
	}
	if !cfg.EnableOTX {
		log.Printf("collector skipping otx: ENABLE_OTX=false")
	} else if len(cfg.OTXTargets) > 0 {
		if cfg.OTXAPIKey == "" {
			log.Printf("collector skipping otx: OTX_TARGETS set but OTX_API_KEY is empty")
		} else {
			providerList = append(providerList, providers.NewOTXProvider(cfg.OTXAPIKey, cfg.OTXTargets))
		}
	}

	if len(providerList) == 0 {
		log.Printf("collector warning: no providers configured; set SHODAN_TARGETS, ABUSEIPDB_TARGETS, OTX_TARGETS, URLHAUS_HOSTS, or CRTSH_QUERY")
	}

	providerStates := make([]*providerState, 0, len(providerList))
	for _, p := range providerList {
		providerStates = append(providerStates, &providerState{name: p.Name(), provider: p})
	}

	interval := time.Duration(cfg.CollectionIntervalSeconds) * time.Second
	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	activeProviders := make([]string, 0, len(providerStates))
	for _, p := range providerStates {
		activeProviders = append(activeProviders, p.name)
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
		cfg.EnableCRTSh && cfg.CRTShQuery != "",
	)

	collectAll := func() {
		ctx, cancel := context.WithTimeout(context.Background(), 90*time.Second)
		defer cancel()

		seenHashes := make(map[string]struct{})
		var seenMu sync.Mutex

		// Buffered channel prevents goroutine blocking on send.
		results := make(chan string, len(providerStates)*2)

		var wg sync.WaitGroup
		wg.Add(len(providerStates))

		for _, state := range providerStates {
			go func() {
				defer wg.Done()

				now := time.Now()
				if now.Before(state.disabledUntil) {
					results <- state.name + " skipped=disabled reason=" + state.disabledReason + " retry_in=" + state.disabledUntil.Sub(now).Round(time.Second).String()
					return
				}

				start := time.Now()
				threats, err := state.provider.Collect(ctx)
				if err != nil {
					kind := providers.ClassifyProviderError(err)
					retryAfter := providers.RetryAfter(err)
					state.consecutiveFailures++

					switch kind {
					case providers.ErrorKindPermanentAuth:
						state.disabledReason = "permanent-auth"
						state.disabledUntil = time.Now().Add(24 * time.Hour)
						results <- state.name + " disabled=24h reason=permanent-auth error=" + err.Error()
					case providers.ErrorKindRateLimited:
						if retryAfter <= 0 {
							retryAfter = 5 * time.Minute
						}
						retryAfter = min(retryAfter, 24*time.Hour)
						state.disabledReason = "rate-limited"
						state.disabledUntil = time.Now().Add(retryAfter)
						results <- state.name + " disabled=" + retryAfter.Round(time.Second).String() + " reason=rate-limited error=" + err.Error()
					case providers.ErrorKindTransient:
						backoff := time.Duration(state.consecutiveFailures*30) * time.Second
						backoff = min(backoff, 10*time.Minute)
						state.disabledReason = "transient"
						state.disabledUntil = time.Now().Add(backoff)
						results <- state.name + " backoff=" + backoff.Round(time.Second).String() + " reason=transient error=" + err.Error()
					default:
						msg := strings.ToLower(err.Error())
						if errors.Is(err, context.DeadlineExceeded) || strings.Contains(msg, "timeout") || strings.Contains(msg, "deadline") {
							backoff := 30 * time.Second
							state.disabledReason = "timeout"
							state.disabledUntil = time.Now().Add(backoff)
							results <- state.name + " backoff=" + backoff.String() + " reason=timeout error=" + err.Error()
						} else {
							results <- state.name + " error: " + err.Error()
						}
					}
					return
				}

				if state.consecutiveFailures > 0 || !state.disabledUntil.IsZero() {
					results <- state.name + " recovered after_failures=" + itoa(state.consecutiveFailures)
				}
				state.consecutiveFailures = 0
				state.disabledUntil = time.Time{}
				state.disabledReason = ""

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

				results <- state.name + " collected=" + itoa(len(threats)) +
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
