package api

import (
	"encoding/json"
	"net/http"
	"strconv"

	"github.com/Sahtattou/SPECTER/pkg/models"
)

func (s *Server) handleHealth(w http.ResponseWriter, _ *http.Request) {
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write([]byte(`{"status":"ok"}`))
}

func (s *Server) handleEvents(w http.ResponseWriter, r *http.Request) {
	stage := r.URL.Query().Get("stage")
	limitStr := r.URL.Query().Get("limit")
	var records []models.ThreatRecord
	var err error

	if stage == "" {
		records, err = s.Repo.ListAll(r.Context())
	} else {
		records, err = s.Repo.ListByStage(r.Context(), stage)
	}
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	if limitStr != "" {
		limit, convErr := strconv.Atoi(limitStr)
		if convErr != nil || limit < 0 {
			http.Error(w, "invalid limit query parameter", http.StatusBadRequest)
			return
		}
		if limit < len(records) {
			records = records[:limit]
		}
	}

	_ = json.NewEncoder(w).Encode(records)
}

func (s *Server) handleQuarantined(w http.ResponseWriter, r *http.Request) {
	out, err := s.Repo.ListByStage(r.Context(), "quarantined")
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	_ = json.NewEncoder(w).Encode(out)
}
