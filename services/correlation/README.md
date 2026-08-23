# Team 4 - Correlation & Investigation

Team 4 is responsible for the correlation and investigation layer of the AI-SIEM platform. This module takes raw security alerts, turns them into structured incidents, and returns investigation-ready JSON for downstream teams such as Team 5 and Team 6.

## What Team 4 provides

This module performs the following work:

- Normalizes alerts into a shared schema
- Enriches them with threat, asset, and vulnerability context
- Deduplicates repeated or overlapping signals
- Correlates related alerts into incidents
- Builds incident facts, timelines, evidence, and attack graphs
- Produces root cause suggestions and recommendations
- Returns structured JSON through a lightweight FastAPI service

The implementation is intentionally evidence-driven. It does not invent unsupported events or relationships; every correlation reason, root cause suggestion, MITRE mapping, and graph edge is based on what is actually present in the incoming alerts.

## Team 4 workflow

```text
Alerts
  └─ Normalize
      └─ Enrich
          └─ Deduplicate
              └─ Correlate
                  └─ Score severity and confidence
                      └─ Build incident facts
                          └─ Generate timeline, evidence, and attack graph
                              └─ Produce root cause and recommendations
                                  └─ Return structured incident JSON
```

## Main outputs

Each incident returned by Team 4 includes:

- incident_id
- target
- alert_count
- severity_score
- confidence_score
- confidence_details
- correlation_reasons
- facts
- mitre
- root_cause
- evidence
- timeline
- attack_graph
- alerts

These fields are designed to be consumed directly by the API, the dashboard, or other teams in the platform.

## Project structure

- correlation/: normalization, deduplication, correlation, and severity scoring
- enrichment/: threat intelligence, asset context, and vulnerability enrichment pipeline
- investigation/: timeline, evidence, root cause, attack graph, and report helpers
- api/: analysis helpers, persistence, and FastAPI server
- models/: incident data models
- sample_data/: example alert and incident data
- frontend/: simple HTML incident viewer
- tests/: regression and workflow tests

## Quick start

From the project directory, which is the folder containing this README and the main.py file:

```bash
cd team4-correlation
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the demo:

```bash
python main.py
```

Run the test suite:

```bash
python -m pytest -q
```

Run the API:

```bash
python -m uvicorn api.server:app --reload
```

Then open:
- http://127.0.0.1:8000/docs

## API endpoints

- POST /ingest
- GET /incidents
- PUT /incidents/{incident_id}
- GET /timeline/{incident_id}
- GET /evidence/{incident_id}
- GET /report/{incident_id}
- GET /root-cause/{incident_id}

## Example workflow

1. Send alert data to the /ingest endpoint.
2. Team 4 normalizes, enriches, correlates, and structures the alerts into incidents.
3. Each incident is returned with evidence-based facts, timeline data, attack graph details, and recommendations.
4. The incident data is stored and can be retrieved or updated through the API.

## Team 5 sample payloads

Example request payload:
- [sample_data/team5_payload.json](sample_data/team5_payload.json)

Example response payload:
- [sample_data/team5_response_example.json](sample_data/team5_response_example.json)

These files provide a practical contract example for Team 5 and help validate that Team 4 is returning structured incident facts, evidence, and recommendations in a consistent format.

