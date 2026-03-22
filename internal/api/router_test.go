package api

import (
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestRouterAppliesConfiguredCORSHeaders(t *testing.T) {
	server := &Server{AllowedOrigins: []string{"http://localhost:1420"}}
	handler := server.Router()

	req := httptest.NewRequest(http.MethodGet, "/health", nil)
	req.Header.Set("Origin", "http://localhost:1420")
	res := httptest.NewRecorder()

	handler.ServeHTTP(res, req)

	if got := res.Header().Get("Access-Control-Allow-Origin"); got != "http://localhost:1420" {
		t.Fatalf("expected Access-Control-Allow-Origin header, got %q", got)
	}

	if got := res.Header().Get("Access-Control-Allow-Methods"); got == "" {
		t.Fatalf("expected Access-Control-Allow-Methods to be set")
	}
}

func TestRouterHandlesOptionsPreflight(t *testing.T) {
	server := &Server{AllowedOrigins: []string{"http://localhost:1420"}}
	handler := server.Router()

	req := httptest.NewRequest(http.MethodOptions, "/api/v1/events", nil)
	req.Header.Set("Origin", "http://localhost:1420")
	res := httptest.NewRecorder()

	handler.ServeHTTP(res, req)

	if res.Code != http.StatusNoContent {
		t.Fatalf("expected status %d, got %d", http.StatusNoContent, res.Code)
	}
}
