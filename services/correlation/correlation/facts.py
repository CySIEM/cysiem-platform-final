from collections import Counter
from typing import Any, Dict, List, Optional


def _normalize_text(value: Optional[Any]) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def extract_facts(alerts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract reusable structured facts from alerts without inventing data."""
    ips = []
    hosts = []
    users = []
    processes = []
    techniques = []
    severities = []

    for alert in alerts:
        if not isinstance(alert, dict):
            continue
        if alert.get("source_ip"):
            ips.append(str(alert.get("source_ip")))
        if alert.get("destination_ip"):
            ips.append(str(alert.get("destination_ip")))
        if alert.get("target"):
            hosts.append(str(alert.get("target")))
        if alert.get("host"):
            hosts.append(str(alert.get("host")))
        if alert.get("username"):
            users.append(str(alert.get("username")))
        if alert.get("process_name"):
            processes.append(str(alert.get("process_name")))
        if alert.get("processes"):
            processes.extend([str(item) for item in alert.get("processes", []) if item])
        if alert.get("mitre"):
            mitre = alert.get("mitre")
            if isinstance(mitre, dict):
                techniques.append(mitre.get("technique", ""))
            elif isinstance(mitre, list):
                for item in mitre:
                    if isinstance(item, dict):
                        techniques.append(item.get("technique", ""))
        severity = alert.get("severity")
        if severity is not None:
            severities.append(str(severity))

    return {
        "ips": list(dict.fromkeys(item for item in ips if item)),
        "hosts": list(dict.fromkeys(item for item in hosts if item)),
        "users": list(dict.fromkeys(item for item in users if item)),
        "processes": list(dict.fromkeys(item for item in processes if item)),
        "techniques": list(dict.fromkeys(item for item in techniques if item)),
        "severity_counts": dict(Counter(severities)),
    }
