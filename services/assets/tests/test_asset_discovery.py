from app.core.risk_engine import RiskFactors, compute_risk_score, score_to_severity


def test_risk_score_bounds():
    factors = RiskFactors(critical_vulns=10, ioc_matches=10)
    score = compute_risk_score(factors)
    assert score == 100


def test_risk_score_severity_bands():
    assert score_to_severity(10) == "low"
    assert score_to_severity(30) == "medium"
    assert score_to_severity(60) == "high"
    assert score_to_severity(90) == "critical"
