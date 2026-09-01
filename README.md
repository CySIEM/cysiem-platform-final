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

## What CySIEM Does

CySIEM ingests raw security logs, figures out what assets/users/IPs are
involved, uses an AI model to judge whether an event is malicious, groups
related events into incidents, investigates them (timeline, root cause,
evidence, attack graph), retrieves relevant security knowledge for that
specific incident, has an AI Copilot explain it in plain language with
recommended actions, and surfaces all of that on an analyst dashboard -
with a safe, simulated response-action trigger. The whole chain is proven
working end-to-end, not just unit-tested in isolation - see
[docs/integration-report.md](docs/integration-report.md) Section I for a
real request/response transcript of an actual run.

## Main Features

- Real log parsing (Linux auth.log, Windows Event Log, network flow) and
  normalization into a shared event schema
- Entity extraction and asset resolution (users, hosts, IPs, processes,
  IOCs, vulnerabilities) with a queryable relationship graph
- AI-based threat classification using a dedicated cybersecurity SLM, with
  MITRE ATT&CK technique mapping
- Rule-based event correlation into incidents, with timeline
  reconstruction, root-cause analysis, evidence aggregation, and attack
  graph generation
- Retrieval-augmented AI Security Copilot: grounds its explanations in an
  actual security knowledge base, not free-form guessing
- A dashboard showing real incidents, severity, risk score, affected
  assets, timeline, and AI explanations - not seeded demo data
- A safe, audit-logged simulated response action per incident

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

### Layers 1-10

| Layer | Name | What it does | Implemented in |
|---|---|---|---|
| 1 | Data Collection | Parses raw logs (SSH auth.log, Windows Event Log JSON, network flow) | `services/collection` |
| 2 | Data Processing | Validates/cleans/normalizes into a shared event schema, forwards to Layer 3 | `services/collection` |
| 3 | Asset Intelligence | Extracts entities, resolves assets, evaluates IOCs/vulnerabilities, builds a relationship graph | `services/assets` |
| 4 | Detection | Classifies events using a security SLM (see Required Models), maps to MITRE ATT&CK | `services/detection` |
| 5 | Correlation | Groups related alerts into incidents by shared host/user/IP/process | `services/correlation` |
| 6 | Investigation | Timeline, root-cause analysis, evidence aggregation, attack graph | `services/correlation` |
| 7 | Knowledge Fabric / RAG | Retrieves relevant security knowledge for a given incident from a FAISS-indexed knowledge base | `services/rag-copilot` |
| 8 | AI Security Copilot | Uses retrieved context + an LLM to explain incidents and recommend actions | `services/rag-copilot` |
| 9 | Visualization Dashboard | Displays real incidents/severity/risk/timeline/AI explanations | `dashboard/frontend` + `dashboard/backend` |
| 10 | Response & Learning | Records a safe, simulated response action per incident (no real-world effect) | `dashboard/backend` |

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
validate this project end-to-end - one command per terminal, 7 terminals
total). Use `python -m uvicorn`, not bare `uvicorn` - on Windows in
particular, pip-installed console scripts often land in a `Scripts`
directory that isn't on `PATH`, so the bare `uvicorn` command fails with
"not recognized" even though it's installed; `python -m uvicorn` always
works because it doesn't depend on `PATH` at all, only on `uvicorn` being
importable by whichever `python` you're invoking.

PowerShell:

```powershell
cd services\collection;  python -m uvicorn app:app --port 8010
cd services\assets;      .venv\Scripts\python.exe -m uvicorn app.main:app --port 8001
cd services\detection;   python -m uvicorn app:app --port 8012
cd services\correlation; python -m uvicorn api.server:app --port 8013
cd services\rag-copilot; python -m uvicorn app:app --port 8014
cd dashboard\backend;    python -m uvicorn api.main:app --port 8000
cd dashboard\frontend;   npm run dev
```

macOS/Linux (bash):

```bash
cd services/collection   && python -m uvicorn app:app --port 8010
cd services/assets       && .venv/bin/python -m uvicorn app.main:app --port 8001
cd services/detection    && python -m uvicorn app:app --port 8012
cd services/correlation  && python -m uvicorn api.server:app --port 8013
cd services/rag-copilot  && python -m uvicorn app:app --port 8014
cd dashboard/backend     && python -m uvicorn api.main:app --port 8000
cd dashboard/frontend    && npm run dev
```

Every service reads its config from its own `.env` - copy each
`.env.example` first. `services/detection` and `dashboard/backend` also
need `CORRELATION_URL`/`RAG_URL` set (either in `.env` or as environment
variables) so they can reach their sibling services - see Environment
Variables below.

## Dashboard

Once `dashboard/frontend` and `dashboard/backend` are both running, open:

**http://localhost:5173**

Register a user (the first one registered becomes `admin`), then log in.
The Incidents tab shows real incidents produced by the pipeline - click
one to see its AI-generated explanation, risk score, and recommended
actions, and to trigger a simulated response action.

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

## Troubleshooting

Real issues hit while building and validating this project, and how they
were actually fixed - not hypothetical:

- **`uvicorn: The term 'uvicorn' is not recognized...`** (PowerShell) -
  the console script isn't on `PATH`. Use `python -m uvicorn ...` instead
  of bare `uvicorn ...` everywhere (see Starting the System above); it
  doesn't need `PATH` at all.
- **Detection or Copilot calls suddenly return 503 / "could not reach
  Ollama"** after Ollama had been working - Ollama auto-updates and
  restarts itself, and the restarted process may not have the
  `OLLAMA_MODELS` environment variable your original `ollama serve`
  session had, so it looks in the default model directory and finds
  nothing (`ollama list` comes back empty even though your models are
  still on disk). Fix: stop the Ollama process, re-set `OLLAMA_MODELS` to
  wherever your models actually are, and restart `ollama serve` (or the
  Ollama app) in that same shell/environment.
- **`services/assets` fails to `pip install`** with Rust/`link.exe`
  compiler errors (`pydantic-core`, `asyncpg`, `greenlet`) - its pinned
  dependency versions don't have prebuilt wheels for very new Python
  versions (e.g. 3.13/3.14) on Windows, so pip tries to compile from
  source and fails without a Rust/MSVC toolchain. Use Python 3.11 for this
  service specifically: `py -3.11 -m venv .venv` (or `python3.11 -m venv
  .venv` on macOS/Linux), then install into that venv.
- **`services/assets` can't connect to Postgres / `password authentication
  failed`** - check `DATABASE_URL` matches whatever instance you actually
  set up (see PostgreSQL Setup above); if you used
  `scripts/setup_isolated_postgres.ps1`, that's port 5433 with password
  `cysiem_test_pw`, not Postgres's default 5432.
- **A service refuses to bind its port** - something else is already
  using it (a previous run you didn't stop, or another app). Find and
  stop the conflicting process, or run that one service on a different
  port and update the URL any dependent service uses to reach it
  (`CORRELATION_URL`, `RAG_URL`, `ASSETS_URL`, etc.).
- **`orchestrator/run_demo.py` fails at the Detection step** - almost
  always means the detection service can't reach Ollama or the model
  isn't loaded; check `ollama list` shows the model from Required Models
  above, and that `services/detection` is running with
  `DETECTION_BACKEND=ollama` (the default).

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
