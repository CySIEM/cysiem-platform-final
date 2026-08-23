from typing import List, Dict, Any


def collect_evidence(alerts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Build a lightweight evidence package from alerts."""
    evidence_items = []
    for alert in alerts:
        if not isinstance(alert, dict):
            continue
        evidence_items.append({
            "id": alert.get("id") or alert.get("alert_id"),
            "title": alert.get("title"),
            "source": alert.get("source"),
            "target": alert.get("target") or alert.get("host") or alert.get("device"),
            "source_ip": alert.get("source_ip"),
            "destination_ip": alert.get("destination_ip"),
            "username": alert.get("username"),
            "hostname": alert.get("hostname"),
            "processes": alert.get("processes", []),
            "file_hashes": alert.get("file_hashes", []),
            "iocs": alert.get("iocs", []),
            "cves": alert.get("cves", []),
        })

    return {
        "evidence_items": evidence_items,
        "summary": {
            "source_ips": [item.get("source_ip") for item in evidence_items if item.get("source_ip")],
            "hostnames": [item.get("hostname") for item in evidence_items if item.get("hostname")],
            "iocs": [item for item in evidence_items if item.get("iocs")],
        },
    }
