from parsers.linux_auth import parse_linux_auth_line
from parsers.network_flow import parse_network_flow
from parsers.windows_eventlog import parse_windows_event


def test_parse_failed_ssh_password():
    line = "Aug 23 10:15:02 server-01 sshd[1234]: Failed password for invalid user admin from 185.220.101.5 port 51322 ssh2"
    result = parse_linux_auth_line(line)

    assert result["host"] == "server-01"
    n = result["normalized"]
    assert n["outcome"] == "failure"
    assert n["user"] == "admin"
    assert n["src_ip"] == "185.220.101.5"
    assert n["src_port"] == 51322
    assert n["protocol"] == "ssh"


def test_parse_accepted_ssh_password():
    line = "Aug 23 10:16:00 server-01 sshd[1235]: Accepted password for alice from 10.0.0.15 port 51300 ssh2"
    result = parse_linux_auth_line(line)

    n = result["normalized"]
    assert n["outcome"] == "success"
    assert n["user"] == "alice"
    assert n["src_ip"] == "10.0.0.15"


def test_parse_unrecognized_line_returns_none():
    assert parse_linux_auth_line("not a syslog line at all") is None


def test_parse_empty_line_returns_none():
    assert parse_linux_auth_line("") is None


def test_parse_windows_failed_logon():
    event = {
        "EventID": "4625",
        "TimeCreated": "2026-08-23T10:00:00Z",
        "Computer": "WIN-DC01",
        "TargetUserName": "jdoe",
        "IpAddress": "203.0.113.5",
    }
    result = parse_windows_event(event)

    assert result["host"] == "WIN-DC01"
    n = result["normalized"]
    assert n["action"] == "logon"
    assert n["outcome"] == "failure"
    assert n["user"] == "jdoe"
    assert n["src_ip"] == "203.0.113.5"


def test_parse_windows_unknown_event_id_still_returns_event():
    result = parse_windows_event({"EventID": "9999", "Computer": "HOST-X"})
    assert result is not None
    assert result["normalized"]["action"] == "event_9999"


def test_parse_windows_missing_event_id_returns_none():
    assert parse_windows_event({"Computer": "HOST-X"}) is None


def test_parse_network_flow_blocked():
    flow = {
        "src_ip": "45.142.212.100",
        "dst_ip": "10.0.0.20",
        "src_port": 4444,
        "dst_port": 443,
        "protocol": "tcp",
        "action": "deny",
    }
    result = parse_network_flow(flow)

    n = result["normalized"]
    assert n["outcome"] == "blocked"
    assert n["dest_ip"] == "10.0.0.20"
    assert n["dest_port"] == 443


def test_parse_network_flow_missing_ips_returns_none():
    assert parse_network_flow({"protocol": "tcp"}) is None
