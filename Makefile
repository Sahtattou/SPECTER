SHELL := /usr/bin/env bash
.SHELLFLAGS := -euo pipefail -c

PYTHON := .venv/bin/python
PIP := $(PYTHON) -m pip

.PHONY: default help \
	setup venv agents-install dashboard-install test-py-install \
	run-api run-worker run-collector run-local \
	build-api build-worker build-collector build \
	run-agents run-dashboard \
	test-go test-py test \
	fmt vet tidy lint check-go check ci-check \
	seed demo-rehearse offline-load bundle clean bootstrap

default: help

help:
	@printf "Available targets:\n"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z0-9_.-]+:.*##/ {printf "  %-18s %s\n", $$1, $$2}' Makefile

setup: ## Create .env from example if missing
	@if [ ! -f .env ]; then cp .env.example .env; fi

venv: ## Create Python virtual environment if missing
	@if [ ! -d .venv ]; then python3 -m venv .venv; fi

agents-install: venv ## Install Python dependencies for agents service
	$(PIP) install -r agents/requirements.txt

dashboard-install: venv ## Install Python dependencies for dashboard
	$(PIP) install streamlit requests

test-py-install: venv ## Install Python test dependency
	$(PIP) install pytest

run-api: ## Run Go API service
	go run ./cmd/api

run-worker: ## Run Go worker service
	go run ./cmd/worker

run-collector: ## Run Go collector service
	go run ./cmd/collector

run-local: ## Run local Go stack via helper script
	./scripts/run_local.sh

build-api: ## Build Go API binary
	mkdir -p bin
	go build -o ./bin/api ./cmd/api

build-worker: ## Build Go worker binary
	mkdir -p bin
	go build -o ./bin/worker ./cmd/worker

build-collector: ## Build Go collector binary
	mkdir -p bin
	go build -o ./bin/collector ./cmd/collector

build: build-api build-worker build-collector ## Build all Go binaries

run-agents: agents-install ## Run Python agents API (uvicorn)
	.venv/bin/uvicorn app.main:app --reload --port 8001 --app-dir agents

run-dashboard: dashboard-install ## Run Streamlit dashboard
	.venv/bin/streamlit run dashboards/streamlit_app.py

test-go: ## Run Go tests
	go test ./... -v

test-py: agents-install test-py-install ## Run Python agents tests
	$(PYTHON) -m pytest agents/tests

test: test-go test-py ## Run all tests

fmt: ## Format Go code
	go fmt ./...

vet: ## Run Go vet
	go vet ./...

tidy: ## Tidy Go module dependencies
	go mod tidy

lint: fmt vet ## Run lint-quality checks for Go

check-go: lint test-go ## Run full Go checks

check: check-go test-py ## Run full repo checks (Go + Python tests)

seed: ## Run demo seed helper script
	./scripts/seed_demo_data.sh

demo-rehearse: ## Run demo smoke rehearsal flow
	./scripts/rehearse_demo.sh

offline-load: ## Load offline snapshot dataset into API
	./scripts/load_offline_snapshot.sh

bundle: ## Create submission artifact bundle directory
	./scripts/create_artifact_bundle.sh

ci-check: ## Run CI-equivalent local checks
	./scripts/ci_check.sh

clean: ## Clean build outputs and Go caches
	go clean -cache -testcache
	rm -rf ./bin

bootstrap: setup venv agents-install dashboard-install test-py-install ## Prepare local environment end-to-end
	@printf "\nBootstrap complete.\n"
	@printf "Next steps:\n"
	@printf "  1) Edit .env if needed\n"
	@printf "  2) Start core services: make run-local\n"
	@printf "  3) Start agents API: make run-agents\n"
	@printf "  4) Start dashboard: make run-dashboard\n"
