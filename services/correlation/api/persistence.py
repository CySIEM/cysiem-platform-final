import json
from pathlib import Path
from typing import Any, Dict, List

STORAGE_PATH = Path(__file__).resolve().parent.parent / "storage" / "incidents.json"


def load_incidents() -> List[Dict[str, Any]]:
    if not STORAGE_PATH.exists():
        return []
    with STORAGE_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_incidents(incidents: List[Dict[str, Any]]) -> None:
    STORAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with STORAGE_PATH.open("w", encoding="utf-8") as handle:
        json.dump(incidents, handle, indent=2)


def upsert_incident(incident: Dict[str, Any]) -> Dict[str, Any]:
    incidents = load_incidents()
    existing = next((item for item in incidents if item.get("incident_id") == incident.get("incident_id")), None)
    if existing is None:
        incidents.append(incident)
    else:
        for key, value in incident.items():
            existing[key] = value
    save_incidents(incidents)
    return incident


def list_incidents() -> List[Dict[str, Any]]:
    return load_incidents()
