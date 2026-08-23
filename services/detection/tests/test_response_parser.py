from response_parser import parse_model_response


def test_parses_clean_json_response():
    text = '{"prediction": "malicious", "confidence": 0.92, "severity": "critical", "mitre": "T1110", "reason": "Repeated failed logins from a known-bad IP."}'
    result = parse_model_response(text)

    assert result["prediction"] == "malicious"
    assert result["confidence"] == 0.92
    assert result["severity"] == "critical"
    assert result["mitre"] == "T1110"


def test_extracts_json_wrapped_in_prose():
    text = 'Here is my analysis:\n{"prediction": "suspicious", "confidence": 0.5, "severity": "medium", "mitre": "", "reason": "Unusual login time."}\nLet me know if you need more.'
    result = parse_model_response(text)

    assert result["prediction"] == "suspicious"
    assert result["severity"] == "medium"


def test_invalid_prediction_value_falls_back_to_suspicious():
    text = '{"prediction": "definitely_bad", "confidence": 0.5, "severity": "medium", "mitre": "", "reason": "x"}'
    result = parse_model_response(text)
    assert result["prediction"] == "suspicious"


def test_unparseable_text_uses_keyword_heuristic_malicious():
    result = parse_model_response("This looks like a ransomware attack in progress.")
    assert result["prediction"] == "malicious"
    assert result["severity"] == "high"


def test_unparseable_text_uses_keyword_heuristic_benign():
    result = parse_model_response("Everything here looks like normal user activity.")
    assert result["prediction"] == "benign"


def test_empty_text_does_not_crash():
    result = parse_model_response("")
    assert result["prediction"] in ("benign", "suspicious", "malicious")
