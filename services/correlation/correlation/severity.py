from typing import Any, Dict, List


def _severity_weight(value: Any) -> int:
    if isinstance(value, (int, float)):
        return max(0, min(100, int(value)))
    if value is None:
        return 20
    text = str(value).strip().lower()
    weights = {"low": 20, "medium": 40, "high": 70, "critical": 100}
    return weights.get(text, 20)


def calculate_severity(alerts: List[Dict[str, Any]]) -> int:
    """Calculate a severity score from alert severity, asset criticality, vulnerabilities and progression."""
    if not alerts:
        return 0

    score = 0
    for alert in alerts:
        score += _severity_weight(alert.get("severity", "low"))

        asset_criticality = str(alert.get("asset_criticality") or "medium").lower()
        criticality_weight = {"low": 0, "medium": 10, "high": 20, "critical": 30}
        score += criticality_weight.get(asset_criticality, 10)

        vulnerabilities = alert.get("cves") or alert.get("vulnerabilities") or []
        if isinstance(vulnerabilities, list):
            score += min(15, len(vulnerabilities) * 5)
        elif vulnerabilities:
            score += 5

        title = str(alert.get("title", "")).lower()
        if "powershell" in title or "ransom" in title:
            score += 10

    average = score // max(1, len(alerts))
    if any(alert.get("severity") == "critical" for alert in alerts):
        return 100
    return min(100, max(10, average))


def calculate_confidence(alerts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Return a confidence score and explainable reasons based on available evidence."""
    if not alerts:
        return {"score": 0, "reasons": ["No alerts were available for correlation"]}

    reasons = []
    score = 40

    if len(alerts) >= 2:
        score += 15
        reasons.append("Multiple alerts support the same incident")
    if any(alert.get("source_ip") for alert in alerts):
        score += 10
        reasons.append("Source or destination IP addresses were present")
    if any(alert.get("username") for alert in alerts):
        score += 10
        reasons.append("User context was present")
    if any(alert.get("process_name") or alert.get("processes") for alert in alerts):
        score += 10
        reasons.append("Process activity was present")
    if any(alert.get("cves") or alert.get("vulnerabilities") for alert in alerts):
        score += 10
        reasons.append("Vulnerability context was present")

    score = min(100, score)
    return {"score": score, "reasons": reasons or ["Basic alert evidence was available"]}
