from typing import Any, Dict, List


def enrich_alerts(alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Add threat, asset, and vulnerability context to each alert."""
    enriched = []
    for alert in alerts:
        if not isinstance(alert, dict):
            continue

        title = str(alert.get("title", "")).lower()
        target = str(alert.get("target") or alert.get("host") or alert.get("device") or "").lower()
        asset_type = "server" if "server" in target or "server" in title or target.startswith("server") else "endpoint"
        if "powershell" in title:
            techniques = ["T1059", "T1055"]
        elif "failed login" in title:
            techniques = ["T1110"]
        else:
            techniques = ["T0000"]

        enriched.append({
            **alert,
            "threat_intelligence": {
                "techniques": techniques,
                "severity_signal": "high" if "powershell" in title else "medium",
            },
            "asset_context": {
                "asset_type": asset_type,
                "asset_name": alert.get("target") or "unknown",
            },
            "vulnerability_context": {
                "cves": [],
                "risk_level": "high" if "powershell" in title else "medium",
            },
        })

    return enriched
