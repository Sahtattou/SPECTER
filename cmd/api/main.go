package main

import (
	"log"
	"net/http"

	"github.com/Sahtattou/SPECTER/internal/api"
	"github.com/Sahtattou/SPECTER/internal/config"
	"github.com/Sahtattou/SPECTER/internal/storage"
)

func main() {
	cfg := config.Load()

	repo, err := storage.NewSQLiteRepository(cfg.DBDSN)
	if err != nil {
		log.Fatalf("init sqlite repository: %v", err)
	}
	defer func() {
		if err := repo.Close(); err != nil {
			log.Printf("close repository: %v", err)
		}
	}()

	server := &api.Server{Repo: repo, AllowedOrigins: cfg.APIAllowedOrigins}

	log.Printf("api listening on :%s", cfg.APIPort)
	if err := http.ListenAndServe(":"+cfg.APIPort, server.Router()); err != nil {
		log.Fatal(err)
	}
}
