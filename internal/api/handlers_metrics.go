package api

import (
	"encoding/json"
	"net/http"
)

func (s *Server) handleMetrics(w http.ResponseWriter, r *http.Request) {
	all, err := s.Repo.ListAll(r.Context())
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	quarantined, _ := s.Repo.ListByStage(r.Context(), "quarantined")
	scored, _ := s.Repo.ListByStage(r.Context(), "scored")

	resp := map[string]any{
		"total_events":      len(all),
		"quarantined_count": len(quarantined),
		"scored_count":      len(scored),
	}
	_ = json.NewEncoder(w).Encode(resp)
}
