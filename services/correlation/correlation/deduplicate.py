from typing import List, Dict, Any


def _alert_identity(alert: Dict[str, Any]) -> tuple:
    """Build a stable identity for an alert even when some fields are missing."""
    return (
        alert.get("id")
        or alert.get("alert_id")
        or alert.get("event_id")
        or alert.get("title"),
        alert.get("source"),
        alert.get("target"),
        alert.get("timestamp"),
    )


def deduplicate_alerts(alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate alerts by a stable identity while preserving order."""
    seen = set()
    unique_alerts = []

    for alert in alerts:
        identity = _alert_identity(alert)
        if identity in seen:
            continue
        seen.add(identity)
        unique_alerts.append(alert)

    return unique_alerts
