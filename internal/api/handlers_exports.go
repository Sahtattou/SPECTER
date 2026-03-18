package api

import (
	"encoding/json"
	"net/http"
	"time"

	"github.com/Sahtattou/SPECTER/internal/ingest"
	"github.com/Sahtattou/SPECTER/internal/output"
	"github.com/Sahtattou/SPECTER/internal/scoring"
	"github.com/Sahtattou/SPECTER/internal/validation"
	"github.com/Sahtattou/SPECTER/pkg/models"
)

func (s *Server) handleExportSTIX(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}

	records, err := s.Repo.ListByStage(r.Context(), "scored")
	if err != nil {
		http.Error(w, "failed to load scored events", http.StatusInternalServerError)
		return
	}

	path, err := output.ExportSTIX(records)
	if err != nil {
		http.Error(w, "failed to generate stix export", http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusAccepted)
	_ = json.NewEncoder(w).Encode(map[string]any{
		"submitted":     true,
		"message":       "stix export generated",
		"records_count": len(records),
		"artifact_path": path,
	})
}

func (s *Server) handleExportReport(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}

	records, err := s.Repo.ListAll(r.Context())
	if err != nil {
		http.Error(w, "failed to load events", http.StatusInternalServerError)
		return
	}

	path, err := output.ExportReport(records)
	if err != nil {
		http.Error(w, "failed to generate report export", http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusAccepted)
	_ = json.NewEncoder(w).Encode(map[string]any{
		"submitted":     true,
		"message":       "report export generated",
		"records_count": len(records),
		"artifact_path": path,
	})
}

type injectionRequest struct {
	IOCType            string         `json:"ioc_type"`
	IOCValue           string         `json:"ioc_value"`
	SourceName         string         `json:"source_name"`
	SourceURL          string         `json:"source_url"`
	SourceQuery        string         `json:"source_query"`
	RawEvidence        map[string]any `json:"raw_evidence"`
	CollectedAt        string         `json:"collected_at"`
	OpenPorts          []int          `json:"open_ports"`
	ASN                string         `json:"asn"`
	CorroborationCount int            `json:"corroboration_count"`
	IsSynthetic        bool           `json:"is_synthetic"`
	PoisonAttackType   string         `json:"poison_attack_type"`
}

func (s *Server) handleInjectionTrigger(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req injectionRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "invalid JSON payload", http.StatusBadRequest)
		return
	}

	if req.IOCType == "" || req.IOCValue == "" {
		http.Error(w, "ioc_type and ioc_value are required", http.StatusBadRequest)
		return
	}

	collectedAt := time.Now().UTC()
	if req.CollectedAt != "" {
		parsed, err := time.Parse(time.RFC3339, req.CollectedAt)
		if err == nil {
			collectedAt = parsed.UTC()
		}
	}

	if req.SourceName == "" {
		req.SourceName = "manual_injection"
	}

	threat := models.Threat{
		IOCValue:         req.IOCValue,
		IOCType:          req.IOCType,
		SourceName:       req.SourceName,
		SourceURL:        req.SourceURL,
		SourceQuery:      req.SourceQuery,
		RawEvidence:      req.RawEvidence,
		CollectedAt:      collectedAt,
		OpenPorts:        req.OpenPorts,
		ASN:              req.ASN,
		Corroboration:    req.CorroborationCount,
		IsSynthetic:      req.IsSynthetic,
		PoisonAttackType: req.PoisonAttackType,
	}

	rec, err := ingest.NormalizeThreat(threat)
	if err != nil {
		http.Error(w, "failed to normalize injected event", http.StatusBadRequest)
		return
	}
	rec = validation.Detect(rec)
	rec = scoring.Score(rec)
	rec.UpdatedAt = time.Now().UTC()

	if err := s.Repo.UpsertRecord(r.Context(), rec); err != nil {
		http.Error(w, "failed to persist injected event", http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusAccepted)
	_ = json.NewEncoder(w).Encode(map[string]any{
		"submitted":    true,
		"message":      "manual injection accepted and persisted",
		"event_id":     rec.EventID,
		"ioc_value":    rec.IOCValue,
		"ioc_type":     rec.IOCType,
		"stage":        rec.PipelineStage,
		"is_synthetic": rec.IsSynthetic,
	})
}
