#!/usr/bin/env bash
# Local dev runner: creates a venv (if missing), installs deps, and starts
# the API with autoreload against a local Postgres (see docker-compose.yml
# to start just the database: `docker-compose up postgres`).
set -euo pipefail

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install -r requirements.txt

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "Created .env from .env.example - edit it before running against a real DB."
fi

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
