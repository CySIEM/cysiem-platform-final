# CySIEM Platform

An AI-powered SIEM pipeline: log collection -> normalization -> asset/entity
intelligence -> AI-based threat detection -> correlation -> investigation ->
RAG-grounded knowledge retrieval -> AI Security Copilot -> dashboard ->
response.

This repository is the result of integrating six teams' independent work
(plus two entirely new services built to fill gaps that had no code at
all). See **[docs/integration-report.md](docs/integration-report.md)** for
the full audit, what was found broken/missing/duplicated, and every
decision made while integrating it - read that first if you're wondering
why something is structured the way it is.

## Architecture

```
Security Data Sources
      |
      v
services/collection    Layer 1-2  Collection & Processing        :8010 (host) / new
      |
      v
services/assets        Layer 3    Asset Intelligence              :8001 (host) / Team 2
      |
      v
services/detection     Layer 4    Detection Fabric (AI/SLM)       :8012 (host) / new
      |
      v
services/correlation   Layer 5-6  Correlation & Investigation     :8013 (host) / Team 4
      |
      v
services/rag-copilot   Layer 7-8  Knowledge Fabric + AI Copilot   :8014 (host) / Team 5
      |
      v
dashboard/backend      Layer 9-10 Dashboard API + bridge          :8000 (host) / Team 6
      |
      v
dashboard/frontend     Layer 9    Dashboard UI                    :5173      / Team 6
```

Each layer is an independently runnable FastAPI service (the dashboard adds
a React frontend), wired together over HTTP rather than merged into one
codebase - see the integration report for why.

## Quick start

```bash
docker compose up --build
# one-time model pull, after ollama is up:
docker exec -it $(docker compose ps -q ollama) ollama pull hf.co/entrick/Security-SLM-Gemma-4-E2B-it-GGUF:Q4_K_M
docker exec -it $(docker compose ps -q ollama) ollama pull llama3.2

python orchestrator/run_demo.py   # runs the full pipeline against a sample attack
```

Or run each service standalone - see each service's own README
(`services/*/README.md`, `dashboard/*/README.md`) for local (non-Docker)
setup, since every service also works independently.

## Services

| Service | Layer(s) | Origin | Port (host) |
|---|---|---|---|
| `services/collection` | 1-2 Collection & Processing | New - no Team 1 code existed | 8010 |
| `services/assets` | 3 Asset Intelligence | Team 2, as-is | 8001 |
| `services/detection` | 4 Detection Fabric | New - no Team 3 code existed | 8012 |
| `services/correlation` | 5-6 Correlation & Investigation | Team 4, as-is | 8013 |
| `services/rag-copilot` | 7-8 Knowledge Fabric + Copilot | Team 5, fixed + extended | 8014 |
| `dashboard/backend` | 9-10 Dashboard API + Response | Team 6, + bridge to correlation/rag-copilot | 8000 |
| `dashboard/frontend` | 9 Dashboard UI | Team 6, as-is | 5173 |

## Known gaps (see integration report for full detail)

- `services/detection`'s primary path needs a live Ollama instance with a
  3.4GB model pulled; the `transformers`-backed fallback avoids that but
  trades off analysis quality.
- `dashboard/backend`'s chart time-series (volume/donut/MITRE/radar) remain
  mocked, as documented in Team 6's own original code.
- `services/assets`'s test suite needs a live Postgres and wasn't run
  against one in this integration pass (credential access issue, not a
  code issue - see the report).
