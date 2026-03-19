package main

import (
	"context"
	"log"
	"os/signal"
	"sync"
	"sync/atomic"
	"syscall"
	"time"

	"github.com/Sahtattou/SPECTER/internal/config"
	"github.com/Sahtattou/SPECTER/internal/scoring"
	"github.com/Sahtattou/SPECTER/internal/storage"
	"github.com/Sahtattou/SPECTER/pkg/models"
)

func main() {
	cfg := config.Load()

	repo, err := storage.NewSQLiteRepository(cfg.DBDSN)
	if err != nil {
		log.Fatalf("init worker repository: %v", err)
	}
	defer func() {
		if err := repo.Close(); err != nil {
			log.Printf("close repository: %v", err)
		}
	}()

	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	concurrency := max(cfg.WorkerConcurrency, 1)
	interval := max(time.Duration(cfg.CollectionIntervalSeconds)*time.Second, 5*time.Second)

	log.Printf("worker started interval=%s concurrency=%d", interval, concurrency)

	processValidated := func() {
		records, err := repo.ListByStage(ctx, "validated")
		if err != nil {
			log.Printf("worker list validated failed: %v", err)
			return
		}
		if len(records) == 0 {
			log.Printf("worker no validated records found")
			return
		}

		jobs := make(chan models.ThreatRecord)
		var wg sync.WaitGroup
		var processed atomic.Int64

		for i := range concurrency {
			wg.Add(1)
			go func(workerID int) {
				defer wg.Done()
				for rec := range jobs {
					rec = scoring.Score(rec)
					now := time.Now().UTC()
					if rec.CreatedAt.IsZero() {
						rec.CreatedAt = now
					}
					rec.UpdatedAt = now

					if err := repo.UpsertRecord(ctx, rec); err != nil {
						log.Printf("worker[%d] upsert failed event=%s err=%v", workerID, rec.EventID, err)
						continue
					}
					processed.Add(1)
				}
			}(i + 1)
		}

		for _, rec := range records {
			select {
			case <-ctx.Done():
				close(jobs)
				wg.Wait()
				return
			case jobs <- rec:
			}
		}

		close(jobs)
		wg.Wait()
		log.Printf("worker processed validated=%d scored=%d", len(records), processed.Load())
	}

	processValidated()

	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			log.Printf("worker shutdown signal received")
			return
		case <-ticker.C:
			processValidated()
		}
	}
}

func max[T ~int | ~int64 | ~float64 | ~int32](a, b T) T {
	if a > b {
		return a
	}
	return b
}
