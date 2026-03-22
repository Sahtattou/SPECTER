package api

import (
	"net/http"
	"strings"

	"github.com/Sahtattou/SPECTER/internal/storage"
)

type Server struct {
	Repo           storage.Repository
	AllowedOrigins []string
}

func (s *Server) Router() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("/health", s.handleHealth)
	mux.HandleFunc("/api/v1/events", s.handleEvents)
	mux.HandleFunc("/api/v1/events/quarantined", s.handleQuarantined)
	mux.HandleFunc("/api/v1/metrics/pipeline", s.handleMetrics)
	mux.HandleFunc("/api/v1/exports/stix", s.handleExportSTIX)
	mux.HandleFunc("/api/v1/exports/report", s.handleExportReport)
	mux.HandleFunc("/api/v1/agents/injections/trigger", s.handleInjectionTrigger)
	return s.withCORS(mux)
}

func (s *Server) withCORS(next http.Handler) http.Handler {
	allowed := make(map[string]struct{}, len(s.AllowedOrigins))
	for _, origin := range s.AllowedOrigins {
		trimmed := strings.TrimSpace(origin)
		if trimmed != "" {
			allowed[trimmed] = struct{}{}
		}
	}

	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		origin := r.Header.Get("Origin")
		if origin != "" {
			if _, ok := allowed[origin]; ok {
				w.Header().Set("Access-Control-Allow-Origin", origin)
				w.Header().Set("Vary", "Origin")
			}
		}
		w.Header().Set("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type,Authorization")
		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusNoContent)
			return
		}
		next.ServeHTTP(w, r)
	})
}
