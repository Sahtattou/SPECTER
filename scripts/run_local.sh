#!/usr/bin/env bash
set -euo pipefail

go run ./cmd/api &
go run ./cmd/worker &
go run ./cmd/collector
