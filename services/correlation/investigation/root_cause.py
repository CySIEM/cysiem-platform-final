from typing import Any, Dict, List


def suggest_root_cause(alerts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Provide an evidence-backed root cause suggestion from observed alerts only."""
    titles = [str(alert.get("title", "")).lower() for alert in alerts]
    recommendations = []
    observed_steps = []

    if any("failed login" in title for title in titles):
        observed_steps.append("Failed login activity")
        recommendations.append("Review authentication logs and reset impacted credentials")
    if any("powershell" in title for title in titles):
        observed_steps.append("PowerShell execution")
        recommendations.append("Inspect the host for suspicious script activity")
    if any("suspicious process" in title for title in titles):
        observed_steps.append("Suspicious process execution")
        recommendations.append("Collect process and memory evidence from the affected host")

    if not observed_steps:
        return {
            "root_cause": "Insufficient evidence to propose a root cause",
            "attack_chain": ["Initial Access"],
            "recommendations": ["Gather more alert context before escalation"],
        }

    root_cause = " and ".join(observed_steps)
    return {
        "root_cause": f"Observed evidence suggests: {root_cause}",
        "attack_chain": observed_steps,
        "recommendations": recommendations or ["Review additional evidence"],
    }
