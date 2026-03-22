package api

import (
	"encoding/json"
	"net/http"
	"time"
)

func (s *Server) handleMetrics(w http.ResponseWriter, r *http.Request) {
	all, err := s.Repo.ListAll(r.Context())
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	quarantined, _ := s.Repo.ListByStage(r.Context(), "quarantined")
	scored, _ := s.Repo.ListByStage(r.Context(), "scored")
	freshness, err := s.Repo.GetFreshnessSummary(r.Context())
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	now := time.Now().UTC()
	freshnessSeconds := any(nil)
	if freshness.LastUpdatedAt != nil {
		freshnessSeconds = int(now.Sub(*freshness.LastUpdatedAt).Seconds())
	}

	perSourceAges := make(map[string]int)
	for source, ts := range freshness.PerSourceFreshness {
		perSourceAges[source] = int(now.Sub(ts).Seconds())
	}

	resp := map[string]any{
		"total_events":                 len(all),
		"quarantined_count":            len(quarantined),
		"scored_count":                 len(scored),
		"last_collected_at":            freshness.LastCollectedAt,
		"last_updated_at":              freshness.LastUpdatedAt,
		"freshness_age_seconds":        freshnessSeconds,
		"distinct_sources":             freshness.DistinctSources,
		"source_freshness_age_seconds": perSourceAges,
	}
	_ = json.NewEncoder(w).Encode(resp)
}
