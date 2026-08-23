# CySIEM Integration Report

## A. Current Architecture (before integration)

The premise going in - six teams' work in branches/folders ready to merge -
didn't match reality:

- The only git repository (`cysiem-platform`) contained only planning docs.
  Every team branch (`team1-data` ... `team6-dashboard`, `develop`) was
  identical, empty `.gitkeep` scaffolding - no team had ever pushed real
  code to git.
- Actual implementations existed only as four standalone, non-git folders:
  `cysiem-platform-team2-assets`, `-team4-correlation`, `-team5-rag`,
  `-team6-dashboard`.
- **Team 1 (Layers 1-2) and Team 3 (Layer 4) had no code anywhere** on the
  machine this integration was performed on.
- Every cross-team JSON contract documented in the original
  `docs/api-contracts.md` was aspirational - no two teams' real code spoke
  the same shape.

## B. Team-by-Team Status (as found)

```
Team 1 (Collection/Processing, L1-2):     MISSING - no code existed anywhere
Team 2 (Asset Intelligence, L3):          PARTIAL - real, solid core logic
Team 3 (Detection/SLM, L4):               MISSING - no code existed anywhere
Team 4 (Correlation/Investigation, L5-6): PARTIAL - real rule-based MVP, 21 passing tests
Team 5 (RAG/Copilot, L7-8):               PARTIAL - real RAG built, disconnected from the live API; mandated HF SLMs absent
Team 6 (Dashboard/Response, L9-10):       PARTIAL - dashboard genuinely wired to a backend; response/automation was a stub
```

**Team 2 (assets)**: FastAPI + Postgres, real regex-based entity extraction,
asset/IOC/vuln enrichment, in-memory graph, risk scoring, API-key auth.
Gaps found: zero Alembic migrations despite full ORM models, no FK
relationships (string-keyed joins only), original output was aggregate
counters rather than entity/relationship arrays.

**Team 4 (correlation)**: FastAPI, no DB (flat JSON file). Real rule-based
correlation (grouping by shared IP/host/user/process), attack-graph
construction that only uses observed edges, timeline, evidence aggregation,
root-cause via a small keyword table, MITRE mapping (2 techniques). All 21
original tests passed, and still pass after being copied into this repo
unchanged.

**Team 5 (RAG/Copilot)**: Real embedding/FAISS/Ollama(`llama3.2`) RAG
pipeline with a small hand-authored 25-file knowledge base - but it was
dead code, never mounted into the actual backend. The live `/ask/`
endpoint was a hardcoded keyword-matcher mock with no LLM or retrieval.
`backend/requirements.txt` was corrupted (UTF-16) and missing
faiss/sentence-transformers/ollama. None of the three manager-mandated
HuggingFace SLMs appeared anywhere in this or any other team's code.

**Team 6 (dashboard)**: React 19 + Vite dashboard genuinely calling a
FastAPI+SQLite backend with JWT auth and live agent polling. But: chart
time-series (volume/donut/MITRE/radar) were static/random mock arrays by
the code's own admission, "Playbooks" execution was a pure frontend
`setTimeout` fake with no backend call, `/copilot/chat` was another
keyword-matcher despite the UI claiming "Powered by RAG," and the actual
response/remediation command channel (`agent/receiver.py.check_commands()`)
was explicitly commented out - a no-op.

## C. Dependency Map (intended vs. actual, before integration)

```
Team1 -> Team2:  intended {timestamp,source_ip,destination_ip,protocol,event}
                 actual:   Team1 didn't exist; Team2's /ingest/events already
                           expected a different (better-specified) shape
                           with a documented regex fallback for raw lines.
Team2 -> Team3:  intended {user,device,asset,ip,vulnerabilities,ioc}
                 actual:   Team3 didn't exist; Team2 exposed GET /entities,
                           /assets, /graph/export instead.
Team3 -> Team4:  intended {prediction,confidence,mitre,reason}
                 actual:   Team4 ingested raw alert dicts directly, no
                           adapter for a detection-model output shape.
Team4 -> Team5:  intended {incident_id,severity,timeline,attack_chain}
                 actual:   Team5's only exposed endpoint took {question:str};
                           no incident-shaped endpoint existed.
Team5 -> Team6:  intended {summary,recommendation,references,cve,mitre}
                 actual:   Team6's /copilot/chat was independent of Team5
                           entirely - its own separate mock.
```

Every cross-team contract in the original docs was aspirational - each team
built against its own assumptions in isolation, with no two ever actually
tested against each other.

## D. Conflicts Found

- **Ports**: Team 2 and Team 6 backends both defaulted to 8000; Team 4's
  README also assumed 8000; Team 5 had two separate `app.py` objects (main
  backend + standalone copilot script) that would also both default to
  8000 if run together.
- **Databases**: Postgres (Team 2), SQLite (Team 6), a flat JSON file
  (Team 4), no persistence at all in Team 5's live backend.
- **Auth**: API-key header (Team 2) vs JWT (Team 6) vs none (Team 4, Team 5).
- **Duplicate/dead implementations**: Team 5 had two parallel copilot
  implementations (real RAG+Ollama script vs. mock keyword-matcher actually
  exposed). Team 5's `backend/` also contained draft dashboard/alerts/
  threats/reports/assets/investigation routers duplicating Teams 2/4/6's
  actual scope. Team 6 had a dead hardcoded `API_URL` constant in
  `App.jsx` duplicating the real configurable `api.js` baseURL.
- **Missing/broken dependencies**: Team 5's `backend/requirements.txt` was
  UTF-16-corrupted and missing its own core libraries.
- **Manager requirement violated**: none of the three specified HuggingFace
  security SLMs were used anywhere.

## E. Integration Plan (executed)

Rather than merge codebases (high risk to working, tested code - especially
Team 4's 21 passing tests), each team's service was kept independently
runnable and wired together via HTTP, all under the one real git repo, on
an `integration` branch off `main`:

```
cysiem-platform/
├── services/
│   ├── collection/    NEW  - Layers 1-2
│   ├── assets/        Team 2, copied as-is
│   ├── detection/      NEW  - Layer 4
│   ├── correlation/   Team 4's real `team4-correlation/` subfolder, as-is
│   └── rag-copilot/   Team 5's ai-services (RAG) + copilot routes only
├── dashboard/
│   ├── backend/        Team 6 backend + bridge.py
│   └── frontend/       Team 6 React app, as-is
├── orchestrator/       NEW - end-to-end demo/pipeline runner
├── docs/
├── docker-compose.yml
└── .env.example
```

Order integrated: collection -> assets (already had a defined ingest
contract) -> detection -> correlation (adapter built to match its actual
field names) -> rag-copilot (fixed + extended) -> dashboard (bridge added).

**Scope decision on Team 5**: only `routes/copilot.py` and `ai-services/`
were integrated. The overlapping dashboard/alerts/threats/reports/assets/
investigation routers in Team 5's `backend/` were left out - Layer 7-8 is
RAG + Copilot only per the project's own team breakdown, and those routers
duplicate Team 2/4/6's actual scope. They still exist in the original
`cysiem-platform-team5-rag` folder; nothing was deleted.

## F. Changes Made

**New services (Team 1 and Team 3 didn't exist; built from scratch):**

- `services/collection/` - FastAPI service producing exactly
  `services/assets`'s existing `NormalizedEvent` contract. Three real
  parsers (`parsers/linux_auth.py`, `windows_eventlog.py`,
  `network_flow.py`), validation/cleaning, batch-forwarding to the assets
  service. 15 tests.
- `services/detection/` - FastAPI service, `POST /detect`. Calls Ollama
  against one of the two mandated Gemma GGUF models by default
  (`hf.co/entrick/Security-SLM-Gemma-4-E2B-it-GGUF:Q4_K_M`, confirmed via
  the model's actual HF repo that it ships its own Ollama Modelfile and is
  pullable directly - no manual Modelfile authoring needed), with a second,
  genuinely wired `transformers`-based backend for the third mandated model
  (`sathishphdai/cybersecurity-slm-5m`, which is not GGUF/Ollama-loadable).
  Response parsing with a keyword-heuristic fallback for malformed model
  output. An adapter (`adapter.py`) maps results into
  `services/correlation`'s actual alert-dict field names (read directly
  from its source, since it has no formal schema) and auto-forwards. 13 tests.

**Fixes to existing team code:**

- `services/rag-copilot/requirements.txt` - was UTF-16-corrupted and
  missing faiss/sentence-transformers/ollama; rewritten.
- `services/rag-copilot/rag/retriever.py` - fixed a cwd-relative FAISS
  index path that only worked when launched from one specific directory.
- `services/rag-copilot/services/copilot_service.py` - replaced the
  hardcoded keyword-matcher mock (`team5_service.py`) with the real
  retriever+Ollama pipeline Team 5 had already built but never wired in.
- `services/rag-copilot` - added `POST /copilot/explain-incident`
  (the Layer 8 -> 9 contract: incident in, `{summary, severity, risk_score,
  recommended_actions, references}` out). 6 tests.
- `dashboard/backend/api/bridge.py` (new) - live-syncs
  `services/correlation`'s incidents into the dashboard's own `Incident`
  table (upsert by incident_id) on every `/api/dashboard/init` call, and
  proxies `/api/copilot/chat` to the real rag-copilot service (falling back
  to the original canned strings only if that service is unreachable).
  Wired into `dashboard/backend/api/main.py`. 6 tests.
- Added missing `Dockerfile`s for `services/correlation`, `dashboard/backend`,
  `dashboard/frontend` (none of the three had one).
- Root `docker-compose.yml`, root `.env.example`, root `.gitignore`, root
  `README.md`.
- `orchestrator/run_demo.py` - drives the full section-12 trace end to end
  over HTTP against all six services.

**Explicitly left unchanged / out of scope:**

- Team 6's mocked chart time-series and simulated Playbook execution.
- Team 5's overlapping dashboard/alerts/etc. routers (see section E).
- `services/assets` and `services/correlation` internals - copied as-is,
  no logic changes, since both already worked and were tested.

## G. Testing Result

| Suite | Result |
|---|---|
| `services/collection` (new, 15 tests) | **15 passed** |
| `services/detection` (new, 13 tests) | **13 passed** |
| `services/rag-copilot` (6 tests, incl. the retriever path-fix regression test) | **6 passed** |
| `services/correlation` (Team 4's original 21 tests, unchanged) | **21 passed** |
| `dashboard/backend` (new bridge smoke tests, 6 tests) | **6 passed** |
| `dashboard/frontend` `npm run build` | **succeeded** (pre-existing bundle-size warning only, not introduced here) |
| `services/assets` (Team 2's original pytest suite) | **not run** - needs a live Postgres; one is installed on this machine but its credentials weren't available and guessing at them wasn't attempted. `python -m py_compile` over the full `app/` tree passed (no syntax/import-order errors). |
| Full `orchestrator/run_demo.py` live run | **not run** - requires Docker and a running Ollama with the 3.4GB mandated model pulled, neither of which is available in this environment (`docker`/`ollama` commands not found here). The script, adapter logic, response parsing, and every service's HTTP contract it depends on are covered by the unit/integration tests above; a live run needs to happen wherever Docker + Ollama are actually available. |

**Total: 61 of 61 runnable tests passed.** The two gaps (assets' DB-backed
suite, the live orchestrator run) are both infrastructure-availability
issues in this environment, not code issues - see the table for exactly
what's needed to close them.
