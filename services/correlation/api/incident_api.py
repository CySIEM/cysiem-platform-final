from typing import List, Dict, Any

from correlation.correlate import correlate_alerts
from correlation.deduplicate import deduplicate_alerts
from correlation.normalize import normalize_alerts
from correlation.severity import calculate_confidence, calculate_severity
from enrichment.pipeline import enrich_alerts
from investigation.attack_graph import build_attack_graph
from investigation.evidence import collect_evidence
from investigation.root_cause import suggest_root_cause
from investigation.timeline import build_timeline


def _mitre_mapping(alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    titles = [str(alert.get("title", "")).lower() for alert in alerts]
    mappings = []
    if any("failed login" in title for title in titles):
        mappings.append({"technique": "T1110", "name": "Brute Force"})
    if any("powershell" in title for title in titles):
        mappings.append({"technique": "T1059", "name": "Command and Scripting Interpreter"})
    if not mappings:
        return [
            {
                "technique": None,
                "name": "Unclassified",
                "status": "insufficient evidence",
                "reason": "No supported ATT&CK technique could be mapped from the provided alerts",
            }
        ]
    return mappings


def analyze_incidents(alerts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Return a structured incident analysis payload suitable for analyst consumption."""
    normalized_alerts = normalize_alerts(alerts)
    unique_alerts = deduplicate_alerts(normalized_alerts)
    enriched_alerts = enrich_alerts(unique_alerts)
    incidents = correlate_alerts(enriched_alerts)
    global_timeline = build_timeline(enriched_alerts)
    global_attack_graph = build_attack_graph(enriched_alerts)

    structured_incidents = []
    for index, incident in enumerate(incidents, start=1):
        alert_list = incident.get("alerts", [])
        incident_timeline = build_timeline(alert_list)
        incident_attack_graph = build_attack_graph(alert_list)
        severity_score = calculate_severity(alert_list)
        confidence = calculate_confidence(alert_list)
        root_cause_details = suggest_root_cause(alert_list)
        evidence_package = collect_evidence(alert_list)
        structured_incidents.append({
            "incident_id": f"INC-{index:03d}",
            "target": incident.get("target", "unknown"),
            "summary": incident.get("summary", "Potential incident"),
            "status": "open",
            "alert_count": len(alert_list),
            "severity_score": severity_score,
            "confidence_score": confidence.get("score") if isinstance(confidence, dict) else confidence,
            "confidence_details": confidence if isinstance(confidence, dict) else {"score": confidence, "reasons": []},
            "correlation_reasons": incident.get("correlation_reasons", []),
            "facts": incident.get("facts", {}),
            "mitre": _mitre_mapping(alert_list),
            "root_cause": root_cause_details,
            "evidence": evidence_package,
            "timeline": incident_timeline,
            "attack_graph": incident_attack_graph,
            "alerts": alert_list,
        })

    return {
        "alert_count": len(unique_alerts),
        "incident_count": len(structured_incidents),
        "incidents": structured_incidents,
        "timeline": global_timeline,
        "attack_graph": global_attack_graph,
        "evidence": {
            "summary": {
                "ips": sorted({item for incident in structured_incidents for item in incident.get("facts", {}).get("ips", [])}),
                "hosts": sorted({item for incident in structured_incidents for item in incident.get("facts", {}).get("hosts", [])}),
                "users": sorted({item for incident in structured_incidents for item in incident.get("facts", {}).get("users", [])}),
            }
        },
        "report": {
            "summary": "Evidence-based incident analysis completed",
            "recommendations": [item.get("root_cause", {}).get("recommendations", []) for item in structured_incidents if item.get("root_cause")],
        },
    }
