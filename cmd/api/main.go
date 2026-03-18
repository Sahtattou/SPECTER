package main

import (
	"log"
	"net/http"

	"github.com/Sahtattou/SPECTER/internal/storage"
)

func main() {
	repo, err := storage.InitDB("./specter_intelligence.db")
	if err != nil {
		log.Fatalf("Failed to initialize database: %v", err)
	}
	defer repo.DB.Close()

	mux := http.NewServeMux()

	mux.HandleFunc("GET /health", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(`{"status": "SPECTER GO API ONLINE"}`))
	})

	log.Println("[*] SPECTER Go API Server running on http://localhost:8080")
	log.Fatal(http.ListenAndServe(":8080", mux))
}
