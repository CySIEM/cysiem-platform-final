from typing import List, Dict, Any


def build_timeline(alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return alerts sorted chronologically by timestamp, ignoring malformed entries."""
    valid_alerts = [alert for alert in alerts if isinstance(alert, dict)]
    return sorted(valid_alerts, key=lambda item: str(item.get("timestamp", "")))
