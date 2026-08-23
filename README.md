# CySIEM Platform

An AI-powered SIEM pipeline: log collection -> normalization -> asset/entity
intelligence -> AI-based threat detection -> correlation -> investigation ->
RAG-grounded knowledge retrieval -> AI Security Copilot -> dashboard ->
response.

**Status: working end-to-end MVP**, verified by an actual pipeline run (not
just unit tests) - see [docs/integration-report.md](docs/integration-report.md)
Section H/I for the full validation record, including request/response
data from the real run.

This repository is the result of integrating six teams' independent work
(plus two entirely new services built to fill gaps that had no code at
all). Read [docs/integration-report.md](docs/integration-report.md) first
if you're wondering why something is structured the way it is - it has the
full audit, every bug found and fixed, and every integration decision made.

## Architecture

```
Security Data Sources
      |
      v
services/collection    Layer 1-2  Collection & Processing        :8010 / new
      |
      v
services/assets        Layer 3    Asset Intelligence              :8001 / Team 2
      |
      v
services/detection     Layer 4    Detection Fabric (AI/SLM)       :8012 / new
      |
      v
services/correlation   Layer 5-6  Correlation & Investigation     :8013 / Team 4
      |
      v
services/rag-copilot   Layer 7-8  Knowledge Fabric + AI Copilot   :8014 / Team 5
      |
      v
dashboard/backend      Layer 9-10 Dashboard API + bridge + response record :8000 / Team 6
      |
      v
dashboard/frontend     Layer 9    Dashboard UI                    :5173      / Team 6
```

Each layer is an independently runnable FastAPI service (the dashboard adds
a React frontend), wired together over HTTP rather than merged into one
codebase - see the integration report for why. Ports listed are the ones
used consistently across `docker-compose.yml`, every service's
`.env.example`, and `orchestrator/run_demo.py`.

## Installation

Requires: Python 3.11 (services/assets specifically needs 3.11 - its pinned
dependencies don't have prebuilt wheels for newer Pythons like 3.13/3.14 on
Windows), Node.js 18+, PostgreSQL client tools (for Layer 3), Ollama (for
real AI inference in Layers 4/8).

```bash
# Per-service Python deps (repeat for each service/ directory):
cd services/collection && pip install -r requirements.txt
cd services/assets && python3.11 -m venv .venv && .venv/bin/pip install -r requirements.txt   # Windows: .venv\Scripts\pip
cd services/detection && pip install -r requirements.txt
cd services/correlation && pip install -r requirements.txt
cd services/rag-copilot && pip install -r requirements.txt
cd dashboard/backend && pip install -r requirements.txt

# Frontend
cd dashboard/frontend && npm install
```

## PostgreSQL Setup (Layer 3 / services/assets)

`services/assets` is the only service needing a database. It auto-creates
its own tables on startup (no Alembic migrations exist yet - see the
integration report) - you just need a reachable empty Postgres database.

**If you don't already have a Postgres instance you want to use**, create
an isolated one dedicated to CySIEM (safe on a machine that already has
Postgres installed elsewhere - separate data directory, separate port,
never touches anything else):

```powershell
pwsh scripts/setup_isolated_postgres.ps1
```

This creates a cluster at `E:\CysiemPgData` (override with `-DataDir`)
listening on port **5433** (not Postgres's default 5432, specifically to
avoid colliding with any existing install), with role `cysiem` / password
`cysiem_test_pw` / database `cysiem_layer3` - already the default in
`services/assets/.env.example`. Stop it with:
`& "C:\Program Files\PostgreSQL\18\bin\pg_ctl.exe" -D "E:\CysiemPgData" stop`

**If you already have Postgres and superuser access you're fine using**,
run `scripts/setup_test_postgres.sql` against it instead (additive only -
creates the `cysiem` role/`cysiem_layer3` database, doesn't touch anything
else): `psql -U postgres -h localhost -f scripts/setup_test_postgres.sql`

## Ollama Setup (Layers 4 and 8)

```bash
# Install: winget install Ollama.Ollama   (or see ollama.com for other OSes)
ollama pull hf.co/entrick/Security-SLM-Gemma-4-E2B-it-GGUF:Q4_K_M   # primary detection model, ~3.4GB
ollama pull llama3.2                                                # copilot model, ~2GB
```

If disk space on your default drive is tight, redirect Ollama's model
storage before pulling: set the `OLLAMA_MODELS` environment variable to a
directory on another drive, then restart the Ollama service/`ollama serve`.

## Required Models

The project manager specified three security SLMs; none may be silently
replaced. Exactly how each one loads (verified by actually loading and
running each, not assumed) is documented in
[services/detection/README.md](services/detection/README.md):

- `entrick/Security-SLM-Gemma-4-E2B-it-GGUF` - **primary**, via Ollama.
- `Nguuma/Security-SLM-Gemma-4-E2B-it-GGUF` - alternate, same mechanism,
  swap in via `DETECTION_MODEL` env var.
- `sathishphdai/cybersecurity-slm-5m` - secondary/fallback backend
  (`DETECTION_BACKEND=transformers`). Not GGUF and not
  `transformers.AutoModelForCausalLM`-compatible - needs its own raw
  PyTorch load path (see the detection service README for why, and how).
  Genuinely verified working, but noticeably slower (~5 min for one
  classification on CPU - no KV-cache in its own reference `generate()`)
  and lower-quality than the Gemma models given its size (~34M params vs
  ~5B). Not used by default or in routine end-to-end demo runs for that
  reason, but fully supported - switch to it with one env var.

## Environment Variables

Each service has its own `.env.example` (copy to `.env` for local runs);
the root `.env.example` covers what `docker-compose.yml` needs. Key ones:

| Variable | Where | Purpose |
|---|---|---|
| `DATABASE_URL` | `services/assets/.env` | Postgres connection - see PostgreSQL Setup above |
| `API_KEY` | `services/assets/.env`, `services/collection/.env` (`ASSETS_API_KEY`) | Shared key for collection -> assets ingest calls |
| `DETECTION_BACKEND`, `DETECTION_MODEL` | `services/detection/.env` | `ollama` (default) or `transformers`; which mandated model to call |
| `CORRELATION_URL` | `services/detection/.env`, `dashboard/backend/.env` | Where to reach the correlation service |
| `RAG_URL` | `dashboard/backend/.env` | Where to reach the RAG/copilot service |
| `COPILOT_MODEL` | `services/rag-copilot/.env` | Ollama model for the Copilot (default `llama3.2`) |
| `JWT_SECRET_KEY` | `dashboard/backend/.env` | Dashboard auth token signing secret |

## Starting the System

**Option A - Docker Compose** (once Docker is available in your
environment; this project's own validation ran natively instead - see
the integration report for why):

```bash
docker compose up --build
docker exec -it $(docker compose ps -q ollama) ollama pull hf.co/entrick/Security-SLM-Gemma-4-E2B-it-GGUF:Q4_K_M
docker exec -it $(docker compose ps -q ollama) ollama pull llama3.2
```

**Option B - run each service natively** (what was actually used to
validate this project end-to-end):

```bash
cd services/collection   && uvicorn app:app --port 8010 &
cd services/assets       && .venv/bin/uvicorn app.main:app --port 8001 &
cd services/detection    && uvicorn app:app --port 8012 &
cd services/correlation  && uvicorn api.server:app --port 8013 &
cd services/rag-copilot  && uvicorn app:app --port 8014 &
cd dashboard/backend     && uvicorn api.main:app --port 8000 &
cd dashboard/frontend    && npm run dev &
```

(Each command needs its own terminal, or background them as shown. Every
service reads its config from its own `.env` - copy each `.env.example`
first.)

## Running the Demo

```bash
python orchestrator/run_demo.py
```

Drives a small, controlled sample scenario (SSH brute-force: repeated
failed logins from `185.220.101.5`, then one successful legitimate login)
through the entire live stack - Collection -> Assets -> Detection ->
Correlation -> RAG -> Copilot - and prints the request/response at each
stage, plus confirms the resulting incident is visible through the
dashboard's own authenticated API. This is the reproducible proof the
pipeline works end-to-end; see Section H/I of the integration report for
a full transcript of an actual run.

## API Endpoints

| Service | Key endpoints |
|---|---|
| `collection` (:8010) | `POST /ingest/raw`, `POST /ingest/file`, `GET /health` |
| `assets` (:8001) | `POST /api/v1/ingest/events`, `GET /api/v1/entities`, `GET /api/v1/assets`, `GET /api/v1/graph/stats`, `GET /api/v1/health` |
| `detection` (:8012) | `POST /detect`, `GET /health` |
| `correlation` (:8013) | `POST /ingest`, `GET /incidents`, `GET /report/{id}`, `GET /timeline/{id}`, `GET /root-cause/{id}` |
| `rag-copilot` (:8014) | `POST /ask/`, `POST /copilot/explain-incident`, `GET /health` |
| `dashboard/backend` (:8000) | `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/dashboard/init`, `GET /api/incidents/{id}/explain`, `POST /api/incidents/{id}/respond`, `GET /api/incidents/{id}/response-history`, `POST /api/copilot/chat` |

## Known MVP Limitations

- `dashboard/backend`'s chart time-series (volume/donut/MITRE/radar) remain
  mocked - Team 6's own original code, documented there and left as-is
  (cosmetic, not part of the incident/detection data path).
- Layer 10 (Response) is intentionally **simulated only** - `POST
  /api/incidents/{id}/respond` records a real, queryable response event
  (who triggered it, which incident, when) but performs no actual
  real-world action (no real IP blocking, account disabling, or host
  isolation), per the project's own safety requirement.
- `services/rag-copilot`'s knowledge base is a small, hand-authored set of
  ~25 markdown files, not a large curated threat-intel corpus.
- No formal Alembic migrations for `services/assets` yet - it auto-creates
  tables on startup in non-production mode.
- `Nguuma/Security-SLM-Gemma-4-E2B-it-GGUF` (the alternate primary-tier
  model) uses the identical loading mechanism as the verified
  `entrick/...` model but wasn't itself pulled and live-tested in this
  validation pass (bandwidth/time, not a technical blocker).
