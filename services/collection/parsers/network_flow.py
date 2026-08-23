"""Parses generic network flow records (JSON dict or a CSV row already split
into a dict by csv.DictReader) into normalized fields. Expected keys:
src_ip/source_ip, dst_ip/destination_ip, src_port, dst_port, protocol,
action/verdict, bytes, timestamp.
"""
from typing import Any, Dict, Optional


def parse_network_flow(flow: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    src_ip = flow.get("src_ip") or flow.get("source_ip")
    dst_ip = flow.get("dst_ip") or flow.get("destination_ip")
    if not src_ip and not dst_ip:
        return None

    def _int_or_none(v):
        try:
            return int(v)
        except (TypeError, ValueError):
            return None

    action = flow.get("action") or flow.get("verdict") or "flow"
    outcome = "blocked" if str(action).lower() in ("deny", "block", "drop", "reject") else "allowed"

    normalized = {
        "event_category": "network",
        "action": action,
        "outcome": outcome,
        "src_ip": src_ip,
        "src_port": _int_or_none(flow.get("src_port")),
        "dest_ip": dst_ip,
        "dest_port": _int_or_none(flow.get("dst_port")),
        "protocol": flow.get("protocol"),
        "message": flow.get("message") or f"{src_ip} -> {dst_ip} ({flow.get('protocol', '?')})",
    }

    return {
        "host": flow.get("host"),
        "event_time": flow.get("timestamp"),
        "normalized": normalized,
        "ocsf_class": "Network Activity",
    }
