#!/usr/bin/env python3
"""End-to-end pipeline demo (task section 12):

  Network Log -> Collection -> Normalization -> Entity Extraction ->
  AI Detection -> Correlation -> Investigation -> RAG Knowledge Retrieval ->
  AI Security Copilot -> Risk Score -> Dashboard Alert -> Recommended Response

Drives every service over HTTP exactly as they'd be wired in
docker-compose.yml, using a synthetic SSH brute-force scenario. Requires
all six services to be running (see docker-compose.yml or each service's
own README for standalone startup) and, for a fully live AI detection +
copilot run, Ollama with the required models pulled - see
services/detection/README.md and services/rag-copilot/README.md.

Usage:
    python orchestrator/run_demo.py
"""
import os
import sys
import time

import requests

COLLECTION_URL = os.getenv("COLLECTION_URL", "http://localhost:8010")
ASSETS_URL = os.getenv("ASSETS_URL", "http://localhost:8001")
ASSETS_API_KEY = os.getenv("ASSETS_API_KEY", "change-me-dev-key")
DETECTION_URL = os.getenv("DETECTION_URL", "http://localhost:8012")
CORRELATION_URL = os.getenv("CORRELATION_URL", "http://localhost:8013")
RAG_URL = os.getenv("RAG_URL", "http://localhost:8014")
DASHBOARD_URL = os.getenv("DASHBOARD_URL", "http://localhost:8000")

# A brute-force SSH login attempt against a known server, immediately
# followed by a successful login - the classic pattern services/correlation
# already has dedicated logic for (see its test suite).
SAMPLE_LOG_LINES = [
    "Aug 23 10:15:01 server-01 sshd[1001]: Failed password for invalid user admin from 185.220.101.5 port 51320 ssh2",
    "Aug 23 10:15:02 server-01 sshd[1002]: Failed password for invalid user admin from 185.220.101.5 port 51321 ssh2",
    "Aug 23 10:15:03 server-01 sshd[1003]: Failed password for invalid user root from 185.220.101.5 port 51322 ssh2",
    "Aug 23 10:15:07 server-01 sshd[1004]: Accepted password for alice from 185.220.101.5 port 51323 ssh2",
]


def step(name):
    print(f"\n=== {name} ===")


def main():
    step("1-2. Collection & Normalization")
    resp = requests.post(
        f"{COLLECTION_URL}/ingest/raw",
        json={"source_type": "linux", "records": SAMPLE_LOG_LINES, "forward": True},
        timeout=30,
    )
    resp.raise_for_status()
    collection_result = resp.json()
    print(f"Normalized {collection_result['events_normalized']} events, forwarded to assets service.")
    print(collection_result["forward_result"])

    step("3. Entity Extraction / Asset Intelligence")
    resp = requests.get(
        f"{ASSETS_URL}/api/v1/entities",
        headers={"X-API-Key": ASSETS_API_KEY},
        timeout=30,
    )
    resp.raise_for_status()
    entities = resp.json()["items"]  # GET /entities is paginated: {items, total, page, page_size}
    print(f"Assets service now knows {len(entities)} entities.")

    step("4. AI Detection")
    # Build a normalized event matching what the collection service would
    # have sent, for the actual brute-force attempt in the sequence (not
    # the final benign successful login) - this is the event that should
    # actually get flagged, correlated into a real incident with a MITRE
    # technique, and explained by the Copilot below.
    detect_event = {
        "event_id": "demo-evt-001",
        "event_time": "2026-08-23T10:15:01+00:00",
        "source": {"host": "server-01", "log_type": "auth_log", "source_type": "linux"},
        "normalized": {
            "action": "ssh_login",
            "outcome": "failure",
            "user": "admin",
            "src_ip": "185.220.101.5",
            "message": "Failed password for invalid user admin from 185.220.101.5, 3rd attempt in 5 seconds",
        },
    }
    resp = requests.post(
        f"{DETECTION_URL}/detect",
        json={"event": detect_event, "entities": entities[:10], "forward": True},
        timeout=60,
    )
    resp.raise_for_status()
    detection_result = resp.json()
    print("Detection:", detection_result["layer4_output"]["detection"])
    print("Forwarded to correlation:", detection_result["forward_result"])

    step("5-6. Correlation & Investigation")
    time.sleep(0.5)
    resp = requests.get(f"{CORRELATION_URL}/incidents", timeout=30)
    resp.raise_for_status()
    incidents = resp.json()
    if not incidents:
        print("No incident was correlated yet - exiting demo early.")
        sys.exit(1)
    incident_id = incidents[-1]["incident_id"]
    resp = requests.get(f"{CORRELATION_URL}/report/{incident_id}", timeout=30)
    resp.raise_for_status()
    report = resp.json()
    print(f"Incident {incident_id}: severity={report['severity']}, attack_type={report['attack_type']}")

    step("7-8. RAG Knowledge Retrieval & AI Security Copilot")
    resp = requests.post(f"{RAG_URL}/copilot/explain-incident", json=report, timeout=60)
    resp.raise_for_status()
    explanation = resp.json()
    print("Copilot summary:", explanation["summary"])
    print("Recommended actions:", explanation["recommended_actions"])
    print("Risk score:", explanation["risk_score"])

    step("9. Dashboard")
    try:
        resp = requests.get(f"{DASHBOARD_URL}/api/dashboard/init", timeout=10)
        if resp.status_code == 401:
            print("Dashboard requires auth - log in via the frontend to see the synced incident;")
            print(f"the bridge pulls it in automatically on the next /api/dashboard/init call ({incident_id}).")
        else:
            resp.raise_for_status()
            print(f"Dashboard now reports {resp.json()['stats']['open_incidents']} open incidents.")
    except requests.RequestException as exc:
        print(f"Dashboard service not reachable ({exc}) - incident {incident_id} is still available via the correlation API.")

    step("10. Recommended Response")
    print("Recommended actions from the Copilot above are what an analyst would action from the dashboard's Playbooks tab.")

    print("\nEnd-to-end pipeline trace complete.")


if __name__ == "__main__":
    main()
