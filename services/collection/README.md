# CySIEM Layer 1/2 - Data Collection & Processing

New service (no Team 1 code existed anywhere in the source repositories
audited for this integration - see /docs/integration-report.md). Built to
produce exactly the `NormalizedEvent` contract that `services/assets`
(Team 2, Layer 3) already implements and documents in its own README, so
integrating required zero changes on the receiving side.

## What it does

Ingests raw security logs, validates/cleans them, and normalizes them into
the shared event schema before forwarding batches to the assets service.
Three real parsers, not stubs:

- `parsers/linux_auth.py` - sshd auth.log lines (failed/accepted password,
  invalid user, connection closed) - regex-based, extracts user/src_ip/
  src_port/outcome.
- `parsers/windows_eventlog.py` - Windows Security Event Log JSON exports
  (4624/4625/4634/4648/4688/4720/4726/4732) - maps EventID to action/outcome.
- `parsers/network_flow.py` - generic network flow JSON (src/dst ip/port,
  protocol, action) for firewall/NetFlow-style sources.

Anything that doesn't match a known pattern is still forwarded as a
minimally-normalized raw event (never silently dropped) so Layer 3's own
regex fallback can still work with it.

## Run

```bash
pip install -r requirements.txt
cp .env.example .env   # point ASSETS_URL/ASSETS_API_KEY at services/assets
uvicorn app:app --reload --port 8000
```

## Endpoints

- `GET /health`
- `POST /ingest/raw` - `{"source_type": "linux"|"windows"|"network",
  "records": [...], "tenant_id": "default", "forward": true}` -> normalizes
  and (if `forward`) POSTs the batch to `services/assets`'s
  `POST /api/v1/ingest/events`.
- `POST /ingest/file` - multipart file upload, one record per line
  (JSON records for windows/network sources).

## Tests

```bash
pytest -v
```
