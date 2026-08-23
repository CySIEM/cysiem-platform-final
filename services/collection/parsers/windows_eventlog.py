"""Parses Windows Security Event Log entries exported as JSON (the shape
`Get-WinEvent | ConvertTo-Json` or a SIEM forwarder typically produces).

Expected input dict keys (all optional except EventID): EventID, TimeCreated,
Computer, SubjectUserName / TargetUserName, IpAddress, LogonType,
ProcessName, NewProcessName, ParentProcessName.
"""
from typing import Any, Dict, Optional

# https://learn.microsoft.com/windows/security/threat-protection/auditing/
_EVENT_ACTIONS = {
    "4624": ("logon", "success"),
    "4625": ("logon", "failure"),
    "4634": ("logoff", "success"),
    "4648": ("logon_explicit_credentials", "success"),
    "4672": ("special_privileges_assigned", "success"),
    "4688": ("process_creation", "success"),
    "4720": ("user_account_created", "success"),
    "4726": ("user_account_deleted", "success"),
    "4732": ("member_added_to_security_group", "success"),
}


def parse_windows_event(event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    event_id = str(event.get("EventID") or event.get("EventId") or "").strip()
    if not event_id:
        return None

    action, outcome = _EVENT_ACTIONS.get(event_id, (f"event_{event_id}", None))

    user = (
        event.get("TargetUserName")
        or event.get("SubjectUserName")
        or event.get("TargetUser")
    )
    process_name = event.get("NewProcessName") or event.get("ProcessName")
    parent_process = event.get("ParentProcessName")
    ip = event.get("IpAddress") or event.get("SourceIp")
    host = event.get("Computer") or event.get("Host")
    event_time = event.get("TimeCreated") or event.get("TimeGenerated")

    normalized: Dict[str, Any] = {
        "event_category": "authentication" if event_id in {"4624", "4625", "4634", "4648"} else "process",
        "action": action,
        "outcome": outcome,
        "user": user,
        "process_name": process_name,
        "parent_process": parent_process,
        "message": f"Windows Security Event {event_id}",
    }
    if ip and ip not in ("-", "::1", "127.0.0.1"):
        normalized["src_ip"] = ip

    return {
        "host": host,
        "event_time": event_time,
        "normalized": normalized,
        "ocsf_class": "Authentication" if "logon" in action or "logoff" in action else "Process Activity",
    }
