# CySIEM Layer 3 - Asset Intelligence Fabric

**Team 2** deliverable for the CySIEM 10-layer SIEM architecture.
Covers: entity extraction, asset discovery, user/device/IP mapping,
vulnerability & threat indicator extraction.

## Quick start (Docker - recommended)

```bash
cp .env.example .env
docker-compose up --build
```

The API will be available at `http://localhost:8000`. Swagger docs at
`http://localhost:8000/docs`.

## Quick start (local Python)

```bash
docker-compose up postgres -d      # start just the database
cp .env.example .env               # edit DATABASE_URL if needed
./scripts/run_dev.sh                # creates venv, installs deps, runs uvicorn
```

## Ingesting real Team 1 exports (normalized JSON)

If you have normalized event exports from Team 1 (Layers 1-2) - the JSON
array shape produced by their pipeline (auditd/Windows eventlog, wrapped in
`source` / `normalized` / `extensions` fields) - POST the array directly:

```bash
curl -X POST http://localhost:8000/api/v1/ingest/events \
  -H "X-API-Key: change-me-dev-key" -H "Content-Type: application/json" \
  -d @your_export_file.json
```

This is the higher-confidence path: it trusts Team 1's already-parsed
fields (host, ip, user, process_name, outcome...) instead of re-deriving
everything with regex, and only regex-sweeps the free-text `message`/`raw`/
`asset.notes` fields for what isn't structured yet (MAC addresses, embedded
hashes/CVEs/domains/URLs).

To validate the extraction logic against a batch of exports **without a
database** (useful before wiring up a new feed):

```bash
python -m scripts.validate_against_real_logs path/to/export1.json path/to/export2.json
```

This prints a full report: events processed, parse errors, entities found
by type, and every asset (host) resolved with its IPs/MACs/usernames/tags.
`tests/fixtures/sample_normalized_events.json` is a small real sample kept
in the repo for exactly this purpose - `tests/test_real_log_sample_regression.py`
runs against it on every test run.

## Try it out

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Ingest a sample log line (replace API key with the one in your .env)
curl -X POST http://localhost:8000/api/v1/ingest/line \
  -H "X-API-Key: change-me-dev-key" \
  -H "Content-Type: application/json" \
  -d '{"raw_line": "sshd: Failed password for user=jdoe from 185.220.101.5 on HOST-FIN01"}'

# List discovered assets
curl http://localhost:8000/api/v1/assets -H "X-API-Key: change-me-dev-key"
```

Or generate a batch of synthetic logs and ingest them all at once:

```bash
python -m scripts.generate_synthetic_logs > sample_logs.txt
```

## Seed sample data

```bash
python -m scripts.seed_data
```

## Running tests

```bash
pip install -r requirements.txt
pytest -v
```

## Database migrations

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

(The app also auto-creates tables on startup in non-production mode for
convenience - disable by setting `APP_ENV=production`.)

## Threat intel feeds (optional)

Set `MISP_URL` / `MISP_API_KEY` and/or `OTX_API_KEY` in `.env` to enable
live threat intel lookups. Without credentials, the service runs in
**stub mode**: IOC checks return "not malicious" instead of failing, so
the whole pipeline is testable offline.

## Project layout

```
app/
├── api/            # FastAPI routers (v1) + shared deps
├── config/         # pydantic-settings configuration
├── core/           # pure logic: extractors, log parsers, graph, risk engine
├── database/       # async SQLAlchemy engine/session, declarative base
├── events/         # outbound event publishing (Kafka, stub-safe)
├── integrations/   # MISP / OTX threat intel clients
├── middleware/      # correlation ID, access logging, error handling
├── models/         # SQLAlchemy ORM models
├── repositories/   # generic + model-specific data access
├── schemas/        # Pydantic request/response contracts
├── security/       # API key + JWT auth
├── services/       # business logic / orchestration
├── telemetry/      # Prometheus metrics + tracing
└── workers/        # scheduled jobs (threat intel sync)
```

See `docs/architecture.md` for the full request flow and
`docs/api_reference.md` for endpoint details.

## Team 2 - Asset Intelligence

| Member | Focus |
|---|---|
| Raghav | Layer 3 |
| Ronak | Layer 3 |
| Alraj | Layer 3 |

Scope: entity extraction, asset discovery, user/device/IP mapping,
vulnerability & threat indicator extraction.
