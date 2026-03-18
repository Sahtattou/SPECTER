package api

import (
	"net/http"

	"github.com/Sahtattou/SPECTER/internal/storage"
)

type Server struct {
	Repo storage.Repository
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
	return mux
}
