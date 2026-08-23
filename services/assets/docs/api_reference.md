# API Reference (Layer 3)

Base path: `/api/v1`. All endpoints except `/health` and `/metrics`
require the `X-API-Key` header (see `API_KEY` in `.env`).

## Health
- `GET /health` - liveness/readiness check
- `GET /metrics` - Prometheus metrics

## Ingestion
- `POST /ingest/line` - `{ "raw_line": "..." }` runs the full pipeline
  on one log line
- `POST /ingest/batch` - `{ "lines": ["...", "..."] }`

## Entities
- `GET /entities` - paginated list, filter by `entity_type`
- `GET /entities/{id}`

## Assets
- `GET /assets` - paginated list, filter by `asset_type`
- `GET /assets/{id}`
- `POST /assets` - manual asset creation
- `POST /assets/{id}/risk-score` - recompute risk score

## IOCs
- `GET /iocs` - paginated list, filter by `is_malicious`
- `GET /iocs/{id}`
- `POST /iocs` - manual IOC creation
- `POST /iocs/sync` - pull latest indicators from configured threat
  intel feeds (MISP/OTX)

## Vulnerabilities
- `GET /vulnerabilities` - paginated list, filter by `severity`
- `GET /vulnerabilities/{id}`
- `POST /vulnerabilities` - enrich and persist a CVE

## Graph
- `GET /graph/stats` - node/edge counts
- `GET /graph/export` - full node-link JSON export
- `GET /graph/neighbors/{entity_type}/{value}` - one-hop neighbors

Interactive docs (Swagger UI): `GET /docs`
