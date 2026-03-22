package storage

import (
	"context"
	"database/sql"
	"embed"
	"encoding/json"
	"errors"
	"time"

	_ "github.com/mattn/go-sqlite3"

	"github.com/Sahtattou/SPECTER/pkg/models"
)

var ErrNotFound = errors.New("record not found")

type Repository interface {
	UpsertRecord(ctx context.Context, rec models.ThreatRecord) error
	ListByStage(ctx context.Context, stage string) ([]models.ThreatRecord, error)
	ListAll(ctx context.Context) ([]models.ThreatRecord, error)
	GetByEventID(ctx context.Context, eventID string) (models.ThreatRecord, error)
	GetFreshnessSummary(ctx context.Context) (FreshnessSummary, error)
	Close() error
}

type FreshnessSummary struct {
	TotalEvents        int
	LastCollectedAt    *time.Time
	LastUpdatedAt      *time.Time
	DistinctSources    int
	PerSourceFreshness map[string]time.Time
}

type SQLiteRepository struct {
	db *sql.DB
}

func NewSQLiteRepository(dsn string) (*SQLiteRepository, error) {
	db, err := sql.Open("sqlite3", dsn)
	if err != nil {
		return nil, err
	}
	db.SetMaxOpenConns(1)
	db.SetMaxIdleConns(1)

	r := &SQLiteRepository{db: db}
	if err := r.migrate(context.Background()); err != nil {
		_ = db.Close()
		return nil, err
	}
	return r, nil
}

//go:embed migrations/*.sql
var migrationFiles embed.FS

func (r *SQLiteRepository) migrate(ctx context.Context) error {

	content, err := migrationFiles.ReadFile("migrations/001_init.sql")

	if err != nil {
		return err
	}

	_, err = r.db.ExecContext(ctx, string(content))
	return err
}

func (r *SQLiteRepository) Close() error { return r.db.Close() }

func (r *SQLiteRepository) UpsertRecord(ctx context.Context, rec models.ThreatRecord) error {
	ports, err := json.Marshal(rec.OpenPorts)
	if err != nil {
		return err
	}

	const q = `
INSERT INTO threat_records (
  event_id, ioc_value, ioc_type, source_name, source_url, source_query,
  raw_evidence_json, collected_at, corroboration_count, open_ports_json, asn,
  is_synthetic, poison_attack_type, poison_detected, detection_rule,
  composite_score, threat_level, days_to_attack, pipeline_stage, created_at, updated_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(event_id) DO UPDATE SET
  ioc_value=excluded.ioc_value,
  ioc_type=excluded.ioc_type,
  source_name=excluded.source_name,
  source_url=excluded.source_url,
  source_query=excluded.source_query,
  raw_evidence_json=excluded.raw_evidence_json,
  collected_at=excluded.collected_at,
  corroboration_count=excluded.corroboration_count,
  open_ports_json=excluded.open_ports_json,
  asn=excluded.asn,
  is_synthetic=excluded.is_synthetic,
  poison_attack_type=excluded.poison_attack_type,
  poison_detected=excluded.poison_detected,
  detection_rule=excluded.detection_rule,
  composite_score=excluded.composite_score,
  threat_level=excluded.threat_level,
  days_to_attack=excluded.days_to_attack,
  pipeline_stage=excluded.pipeline_stage,
  updated_at=excluded.updated_at
`
	_, err = r.db.ExecContext(ctx, q,
		rec.EventID, rec.IOCValue, rec.IOCType, rec.SourceName, rec.SourceURL, rec.SourceQuery,
		rec.RawEvidenceJSON, rec.CollectedAt.UTC(), rec.CorroborationCount, string(ports), rec.ASN,
		boolToInt(rec.IsSynthetic), rec.PoisonAttackType, boolPtrToNullInt(rec.PoisonDetected), rec.DetectionRule,
		rec.CompositeScore, rec.ThreatLevel, rec.DaysToAttack, rec.PipelineStage, rec.CreatedAt.UTC(), rec.UpdatedAt.UTC(),
	)
	return err
}

func (r *SQLiteRepository) ListByStage(ctx context.Context, stage string) ([]models.ThreatRecord, error) {
	const q = `
SELECT event_id, ioc_value, ioc_type, source_name, source_url, source_query,
       raw_evidence_json, collected_at, corroboration_count, open_ports_json, asn,
       is_synthetic, poison_attack_type, poison_detected, detection_rule,
       composite_score, threat_level, days_to_attack, pipeline_stage, created_at, updated_at
FROM threat_records
WHERE pipeline_stage = ?
ORDER BY collected_at DESC
`
	rows, err := r.db.QueryContext(ctx, q, stage)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	return scanRows(rows)
}

func (r *SQLiteRepository) ListAll(ctx context.Context) ([]models.ThreatRecord, error) {
	const q = `
SELECT event_id, ioc_value, ioc_type, source_name, source_url, source_query,
       raw_evidence_json, collected_at, corroboration_count, open_ports_json, asn,
       is_synthetic, poison_attack_type, poison_detected, detection_rule,
       composite_score, threat_level, days_to_attack, pipeline_stage, created_at, updated_at
FROM threat_records
ORDER BY collected_at DESC
`
	rows, err := r.db.QueryContext(ctx, q)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	return scanRows(rows)
}

func (r *SQLiteRepository) GetByEventID(ctx context.Context, eventID string) (models.ThreatRecord, error) {
	const q = `
SELECT event_id, ioc_value, ioc_type, source_name, source_url, source_query,
       raw_evidence_json, collected_at, corroboration_count, open_ports_json, asn,
       is_synthetic, poison_attack_type, poison_detected, detection_rule,
       composite_score, threat_level, days_to_attack, pipeline_stage, created_at, updated_at
FROM threat_records WHERE event_id = ? LIMIT 1
`
	row := r.db.QueryRowContext(ctx, q, eventID)
	rec, err := scanOne(row)
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return models.ThreatRecord{}, ErrNotFound
		}
		return models.ThreatRecord{}, err
	}
	return rec, nil
}

func (r *SQLiteRepository) GetFreshnessSummary(ctx context.Context) (FreshnessSummary, error) {
	const overallQ = `
SELECT COUNT(*), MAX(collected_at), MAX(updated_at), COUNT(DISTINCT source_name)
FROM threat_records
`

	var (
		total           int
		lastCollectedNS sql.NullString
		lastUpdatedNS   sql.NullString
		distinctSources int
	)

	if err := r.db.QueryRowContext(ctx, overallQ).Scan(&total, &lastCollectedNS, &lastUpdatedNS, &distinctSources); err != nil {
		return FreshnessSummary{}, err
	}

	parseTS := func(ns sql.NullString) (*time.Time, error) {
		if !ns.Valid || ns.String == "" {
			return nil, nil
		}
		t, err := time.Parse(time.RFC3339Nano, ns.String)
		if err != nil {
			t, err = time.Parse("2006-01-02 15:04:05.999999999Z07:00", ns.String)
		}
		if err != nil {
			return nil, err
		}
		u := t.UTC()
		return &u, nil
	}

	lastCollectedAt, err := parseTS(lastCollectedNS)
	if err != nil {
		return FreshnessSummary{}, err
	}
	lastUpdatedAt, err := parseTS(lastUpdatedNS)
	if err != nil {
		return FreshnessSummary{}, err
	}

	const perSourceQ = `
SELECT source_name, MAX(updated_at)
FROM threat_records
GROUP BY source_name
`
	rows, err := r.db.QueryContext(ctx, perSourceQ)
	if err != nil {
		return FreshnessSummary{}, err
	}
	defer rows.Close()

	perSource := make(map[string]time.Time)
	for rows.Next() {
		var source string
		var updatedNS sql.NullString
		if err := rows.Scan(&source, &updatedNS); err != nil {
			return FreshnessSummary{}, err
		}
		if !updatedNS.Valid || updatedNS.String == "" {
			continue
		}
		t, err := time.Parse(time.RFC3339Nano, updatedNS.String)
		if err != nil {
			t, err = time.Parse("2006-01-02 15:04:05.999999999Z07:00", updatedNS.String)
		}
		if err != nil {
			return FreshnessSummary{}, err
		}
		perSource[source] = t.UTC()
	}
	if err := rows.Err(); err != nil {
		return FreshnessSummary{}, err
	}

	return FreshnessSummary{
		TotalEvents:        total,
		LastCollectedAt:    lastCollectedAt,
		LastUpdatedAt:      lastUpdatedAt,
		DistinctSources:    distinctSources,
		PerSourceFreshness: perSource,
	}, nil
}

func scanRows(rows *sql.Rows) ([]models.ThreatRecord, error) {
	var out []models.ThreatRecord
	for rows.Next() {
		rec, err := scanWith(rows.Scan)
		if err != nil {
			return nil, err
		}
		out = append(out, rec)
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	return out, nil
}

func scanOne(row interface{ Scan(dest ...any) error }) (models.ThreatRecord, error) {
	return scanWith(row.Scan)
}

func scanWith(scan func(dest ...any) error) (models.ThreatRecord, error) {
	var rec models.ThreatRecord
	var portsJSON string
	var isSyntheticInt int
	var poisonDetected sql.NullInt64
	var composite sql.NullFloat64
	var collectedAt, createdAt, updatedAt time.Time

	err := scan(
		&rec.EventID, &rec.IOCValue, &rec.IOCType, &rec.SourceName, &rec.SourceURL, &rec.SourceQuery,
		&rec.RawEvidenceJSON, &collectedAt, &rec.CorroborationCount, &portsJSON, &rec.ASN,
		&isSyntheticInt, &rec.PoisonAttackType, &poisonDetected, &rec.DetectionRule,
		&composite, &rec.ThreatLevel, &rec.DaysToAttack, &rec.PipelineStage, &createdAt, &updatedAt,
	)
	if err != nil {
		return models.ThreatRecord{}, err
	}

	rec.IsSynthetic = isSyntheticInt == 1
	rec.PoisonDetected = nullIntToBoolPtr(poisonDetected)
	if composite.Valid {
		v := composite.Float64
		rec.CompositeScore = &v
	}
	rec.CollectedAt, rec.CreatedAt, rec.UpdatedAt = collectedAt.UTC(), createdAt.UTC(), updatedAt.UTC()

	if portsJSON == "" {
		portsJSON = "[]"
	}
	if err := json.Unmarshal([]byte(portsJSON), &rec.OpenPorts); err != nil {
		return models.ThreatRecord{}, err
	}

	return rec, nil
}

func boolToInt(v bool) int {
	if v {
		return 1
	}
	return 0
}

func boolPtrToNullInt(v *bool) any {
	if v == nil {
		return nil
	}
	if *v {
		return 1
	}
	return 0
}

func nullIntToBoolPtr(v sql.NullInt64) *bool {
	if !v.Valid {
		return nil
	}
	b := v.Int64 == 1
	return &b
}
