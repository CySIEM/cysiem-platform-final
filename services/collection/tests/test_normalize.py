from normalize import normalize_batch, normalize_raw_line


def test_normalize_raw_line_matches_assets_contract_shape():
    line = "Aug 23 10:15:02 server-01 sshd[1234]: Failed password for invalid user admin from 185.220.101.5 port 51322 ssh2"
    event = normalize_raw_line(line)

    # Exact top-level keys services/assets's NormalizedEvent schema expects.
    for key in ("event_id", "ingested_at", "event_time", "source", "normalized", "raw", "raw_format", "schema_version"):
        assert key in event

    assert event["source"]["host"] == "server-01"
    assert event["source"]["log_type"] == "auth_log"
    assert event["normalized"]["user"] == "admin"
    assert event["normalized"]["src_ip"] == "185.220.101.5"


def test_normalize_raw_line_unrecognized_still_forwards_as_raw_event():
    event = normalize_raw_line("some totally unstructured log text")
    assert event is not None
    assert event["source"]["log_type"] == "raw_line"
    assert event["normalized"]["message"] == "some totally unstructured log text"


def test_normalize_raw_line_empty_returns_none():
    assert normalize_raw_line("   ") is None


def test_normalize_batch_linux():
    lines = [
        "Aug 23 10:15:02 server-01 sshd[1234]: Failed password for invalid user admin from 185.220.101.5 port 51322 ssh2",
        "",
        "Aug 23 10:16:00 server-01 sshd[1235]: Accepted password for alice from 10.0.0.15 port 51300 ssh2",
    ]
    events = normalize_batch(lines, "linux")
    assert len(events) == 2


def test_normalize_batch_network_from_json_strings():
    import json

    flows = [json.dumps({"src_ip": "1.2.3.4", "dst_ip": "5.6.7.8", "protocol": "tcp", "action": "allow"})]
    events = normalize_batch(flows, "network")
    assert len(events) == 1
    assert events[0]["normalized"]["outcome"] == "allowed"


def test_normalize_batch_unknown_source_type_raises():
    import pytest

    with pytest.raises(ValueError):
        normalize_batch(["x"], "carrier_pigeon")
