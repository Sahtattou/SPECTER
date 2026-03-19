set shell := ["bash", "-euo", "pipefail", "-c"]
set dotenv-load := true

# SPECTER task runner

default:
  @just --list

# Setup 

setup:
  @if [ ! -f .env ]; then cp .env.example .env; fi

venv:
  @if [ ! -d .venv ]; then python3 -m venv .venv; fi

agents-install: venv
  .venv/bin/python -m pip install -r agents/requirements.txt

dashboard-install: venv
  .venv/bin/python -m pip install streamlit requests

test-py-install: venv
  .venv/bin/python -m pip install pytest

# Go run/build 

run-api:
  go run ./cmd/api

run-worker:
  go run ./cmd/worker

run-collector:
  go run ./cmd/collector

run-local:
  ./scripts/run_local.sh

build-api:
  mkdir -p bin
  go build -o ./bin/api ./cmd/api

build-worker:
  mkdir -p bin
  go build -o ./bin/worker ./cmd/worker

build-collector:
  mkdir -p bin
  go build -o ./bin/collector ./cmd/collector

build: build-api build-worker build-collector

# Python services 

run-agents: agents-install
  .venv/bin/uvicorn app.main:app --reload --port 8001 --app-dir agents

run-dashboard: dashboard-install
  .venv/bin/streamlit run dashboards/streamlit_app.py

# Tests and quality 

test-go:
  go test ./... -v

test-py: agents-install test-py-install
  .venv/bin/python -m pytest agents/tests

test: test-go test-py

fmt:
  go fmt ./...

vet:
  go vet 

tidy:
  go mod tidy

lint: fmt vet

check-go: lint test-go

check: check-go test-py

# Helpers

seed:
  ./scripts/seed_demo_data.sh

clean:
  go clean -cache -testcache
  rm -rf ./bin
