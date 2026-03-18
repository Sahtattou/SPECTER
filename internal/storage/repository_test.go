package storage

import (
	"context"
	"testing"
	"time"

	"github.com/Sahtattou/SPECTER/pkg/models"
)

func TestSQLiteRepository_UpsertAndRead(t *testing.T) {
	repo, err := NewSQLiteRepository("file::memory:?cache=shared")
	if err != nil {
		t.Fatalf("NewSQLiteRepository error: %v", err)
	}
	defer repo.Close()

	now := time.Now().UTC()
	score := 88.5
	detected := true

	rec := models.ThreatRecord{
		EventID:            "evt-1",
		IOCValue:           "malicious.example",
		IOCType:            "domain",
		SourceName:         "crtsh",
		SourceURL:          "https://crt.sh/",
		SourceQuery:        "%.secure-login",
		RawEvidenceJSON:    `{"id":123}`,
		CollectedAt:        now,
		CorroborationCount: 2,
		OpenPorts:          []int{443, 50050},
		ASN:                "AS13335",
		IsSynthetic:        false,
		PoisonAttackType:   "",
		PoisonDetected:     &detected,
		DetectionRule:      "SINGLE_SOURCE_FRESH_DOMAIN",
		CompositeScore:     &score,
		ThreatLevel:        "critical",
		DaysToAttack:       "0-2",
		PipelineStage:      "scored",
		CreatedAt:          now,
		UpdatedAt:          now,
	}

	if err := repo.UpsertRecord(context.Background(), rec); err != nil {
		t.Fatalf("UpsertRecord error: %v", err)
	}

	got, err := repo.GetByEventID(context.Background(), "evt-1")
	if err != nil {
		t.Fatalf("GetByEventID error: %v", err)
	}

	if got.EventID != rec.EventID {
		t.Fatalf("event_id mismatch: got %s want %s", got.EventID, rec.EventID)
	}
	if len(got.OpenPorts) != 2 || got.OpenPorts[1] != 50050 {
		t.Fatalf("open_ports mismatch: %+v", got.OpenPorts)
	}
	if got.CompositeScore == nil || *got.CompositeScore != score {
		t.Fatalf("composite_score mismatch: %+v", got.CompositeScore)
	}
	if got.PoisonDetected == nil || *got.PoisonDetected != detected {
		t.Fatalf("poison_detected mismatch: %+v", got.PoisonDetected)
	}
}

func TestSQLiteRepository_ListByStage(t *testing.T) {
	repo, err := NewSQLiteRepository("file::memory:?cache=shared")
	if err != nil {
		t.Fatalf("NewSQLiteRepository error: %v", err)
	}
	defer repo.Close()

	now := time.Now().UTC()

	in := []models.ThreatRecord{
		{
			EventID:         "evt-a",
			IOCValue:        "1.1.1.1",
			IOCType:         "ip",
			SourceName:      "abuseipdb",
			RawEvidenceJSON: "{}",
			CollectedAt:     now,
			PipelineStage:   "quarantined",
			CreatedAt:       now,
			UpdatedAt:       now,
		},
		{
			EventID:         "evt-b",
			IOCValue:        "2.2.2.2",
			IOCType:         "ip",
			SourceName:      "shodan",
			RawEvidenceJSON: "{}",
			CollectedAt:     now,
			PipelineStage:   "scored",
			CreatedAt:       now,
			UpdatedAt:       now,
		},
	}

	for _, rec := range in {
		if err := repo.UpsertRecord(context.Background(), rec); err != nil {
			t.Fatalf("UpsertRecord error: %v", err)
		}
	}

	q, err := repo.ListByStage(context.Background(), "quarantined")
	if err != nil {
		t.Fatalf("ListByStage error: %v", err)
	}
	if len(q) != 1 || q[0].EventID != "evt-a" {
		t.Fatalf("unexpected quarantined result: %+v", q)
	}
}
