from typing import Any, Dict, List


def normalize_alerts(alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize alert field names and values for downstream correlation."""
    normalized = []
    for alert in alerts:
        if not isinstance(alert, dict):
            continue

        normalized_alert = dict(alert)
        normalized_alert["target"] = (
            alert.get("target")
            or alert.get("host")
            or alert.get("device")
            or "unknown"
        )
        normalized_alert["severity"] = str(alert.get("severity", "low")).lower()
        normalized_alert["title"] = alert.get("title") or alert.get("name") or "Untitled alert"
        normalized.append(normalized_alert)

    return normalized
