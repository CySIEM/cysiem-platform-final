# Layer 3 - Asset Intelligence Fabric: Architecture

## Position in the CySIEM pipeline
Layer 3 sits between Layer 2 (Data Processing Fabric) and Layer 4
(Detection Fabric). It receives normalized log records and is
responsible for:

- Entity extraction (IPs, hostnames, MACs, usernames, domains, URLs,
  hashes, CVEs, ports, emails)
- Asset discovery via entity resolution (merging co-occurring entities
  into a single logical Asset)
- IOC extraction and threat intel enrichment (MISP, OTX)
- Vulnerability enrichment (CVE association + severity)
- Knowledge graph construction (NetworkX in-process, persisted to
  Postgres for durability)
- Baseline risk scoring per asset

## Request flow
```
Log line
  -> app/core/log_parsers.py       (detect source type, normalize)
  -> app/core/entity_extractor.py  (regex-based entity extraction)
  -> app/services/entity_extraction_service.py (persist Entity rows)
  -> app/services/graph_service.py (build graph edges)
  -> app/services/asset_discovery_service.py   (resolve Asset rows)
  -> app/services/ioc_extraction_service.py    (threat intel lookups)
  -> app/services/vulnerability_enrichment_service.py (CVE severity)
  -> app/events/producer.py        (publish to Kafka, if configured)
```
All of the above is orchestrated by `app/services/ingestion_service.py`
and exposed at `POST /api/v1/ingest/line` and `/ingest/batch`.

## Layered module responsibilities
- `app/api` - FastAPI routers, request/response wiring only
- `app/services` - business logic / orchestration
- `app/repositories` - persistence access (generic + model-specific)
- `app/models` - SQLAlchemy ORM tables
- `app/schemas` - Pydantic request/response contracts
- `app/core` - pure logic with no I/O (extractors, graph, risk engine)
- `app/integrations` - external threat intel clients (stub-mode safe)
- `app/events` - outbound event publishing (Kafka, stubbed if unset)
- `app/workers` - scheduled/background jobs
- `app/security` - API key + JWT auth
- `app/telemetry` - Prometheus metrics + tracing helpers
- `app/middleware` - correlation IDs, access logging, error handling

## Data model
See `app/models/` — `Entity`, `Asset`, `IOC`, `Vulnerability`,
`EntityEdge`, `RiskScore`. Migrations are managed with Alembic
(`alembic/`).

## Running without external dependencies
The service is fully runnable with just Postgres:
- MISP/OTX clients auto-fall-back to stub mode when unconfigured.
- Kafka event publishing no-ops (logs only) when
  `KAFKA_BOOTSTRAP_SERVERS` is unset.
- The knowledge graph runs in-process (NetworkX) with edges also
  persisted to Postgres for durability/audit.
