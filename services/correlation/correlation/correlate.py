from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from correlation.facts import extract_facts


def _parse_timestamp(value: Optional[Any]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def correlate_alerts(alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Group alerts into incidents using shared entities and time proximity."""
    incidents: List[Dict[str, Any]] = []

    if not alerts:
        return incidents

    groups: Dict[Tuple[str, ...], List[Dict[str, Any]]] = defaultdict(list)
    for alert in alerts:
        if not isinstance(alert, dict):
            continue
        target = str(alert.get("target") or alert.get("host") or alert.get("device") or "unknown")
        host = str(alert.get("host") or alert.get("target") or "")
        user = str(alert.get("username") or "")
        src_ip = str(alert.get("source_ip") or "")
        dst_ip = str(alert.get("destination_ip") or "")
        process = str(alert.get("process_name") or "")
        key = (
            target,
            host,
            user,
            src_ip or dst_ip,
            process,
        )
        groups[key].append(alert)

    for key, group_alerts in groups.items():
        sorted_alerts = sorted(group_alerts, key=lambda item: str(item.get("timestamp", "")))
        target = key[0] if key[0] else "unknown"
        reasons = []
        shared_host = key[0] and key[1] and key[0] == key[1]
        shared_user = bool(key[2])
        shared_ip = bool(key[3])
        shared_process = bool(key[4])

        if len(sorted_alerts) > 1:
            reasons.append(f"{len(sorted_alerts)} alerts were grouped together")
        if shared_host:
            reasons.append(f"The alerts share the same host: {key[0]}")
        if shared_user:
            reasons.append(f"The alerts reference the same user: {key[2]}")
        if shared_ip:
            reasons.append(f"The alerts share the same IP: {key[3]}")
        if shared_process:
            reasons.append(f"The alerts reference the same process: {key[4]}")

        if len(sorted_alerts) > 1:
            timestamps = [alert.get("timestamp") for alert in sorted_alerts if alert.get("timestamp")]
            if len(timestamps) >= 2:
                reasons.append(f"The alerts occurred within the observed time window: {timestamps[0]} to {timestamps[-1]}")

        if not reasons:
            reasons.append("The alerts shared a target")

        incidents.append({
            "target": target,
            "alerts": sorted_alerts,
            "summary": f"Potential incident on {target}",
            "correlation_reasons": reasons,
            "facts": extract_facts(sorted_alerts),
        })

    return incidents
