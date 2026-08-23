"""Parses Linux auth.log / secure-log style SSH lines into normalized fields.

Handles the syslog-prefixed lines sshd actually emits, e.g.:
  "Aug 23 10:15:02 server-01 sshd[1234]: Failed password for invalid user
   admin from 185.220.101.5 port 51322 ssh2"
  "Aug 23 10:15:05 server-01 sshd[1234]: Accepted password for alice from
   10.0.0.15 port 51300 ssh2"
"""
import re
from datetime import datetime
from typing import Any, Dict, Optional

_SYSLOG_PREFIX = re.compile(
    r"^(?P<ts>\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+"
    r"(?P<host>\S+)\s+"
    r"(?P<proc>[\w.\-/]+)(?:\[(?P<pid>\d+)\])?:\s*"
    r"(?P<message>.*)$"
)

_FAILED_PASSWORD = re.compile(
    r"Failed password for (?:invalid user )?(?P<user>\S+) from (?P<ip>[\d.]+) port (?P<port>\d+)"
)
_ACCEPTED_PASSWORD = re.compile(
    r"Accepted (?:password|publickey) for (?P<user>\S+) from (?P<ip>[\d.]+) port (?P<port>\d+)"
)
_INVALID_USER = re.compile(r"Invalid user (?P<user>\S+) from (?P<ip>[\d.]+)")
_CONN_CLOSED = re.compile(r"Connection closed by (?:authenticating user \S+ )?(?P<ip>[\d.]+)")


def _parse_syslog_time(ts: str, year: Optional[int] = None) -> Optional[str]:
    year = year or datetime.now().year
    try:
        dt = datetime.strptime(f"{year} {ts}", "%Y %b %d %H:%M:%S")
        return dt.isoformat()
    except ValueError:
        return None


def parse_linux_auth_line(line: str) -> Optional[Dict[str, Any]]:
    """Returns None if the line isn't a recognizable sshd auth log line
    (caller falls back to a raw/unstructured event rather than dropping it).
    """
    line = line.strip()
    if not line:
        return None

    m = _SYSLOG_PREFIX.match(line)
    if not m:
        return None

    host = m.group("host")
    proc = m.group("proc")
    message = m.group("message")
    event_time = _parse_syslog_time(m.group("ts"))

    if proc != "sshd":
        return {
            "host": host,
            "event_time": event_time,
            "normalized": {"message": message, "process_name": proc},
        }

    fm = _FAILED_PASSWORD.search(message)
    if fm:
        return {
            "host": host,
            "event_time": event_time,
            "normalized": {
                "event_category": "authentication",
                "action": "ssh_login",
                "outcome": "failure",
                "user": fm.group("user"),
                "src_ip": fm.group("ip"),
                "src_port": int(fm.group("port")),
                "protocol": "ssh",
                "process_name": "sshd",
                "message": message,
            },
        }

    am = _ACCEPTED_PASSWORD.search(message)
    if am:
        return {
            "host": host,
            "event_time": event_time,
            "normalized": {
                "event_category": "authentication",
                "action": "ssh_login",
                "outcome": "success",
                "user": am.group("user"),
                "src_ip": am.group("ip"),
                "src_port": int(am.group("port")),
                "protocol": "ssh",
                "process_name": "sshd",
                "message": message,
            },
        }

    iu = _INVALID_USER.search(message)
    if iu:
        return {
            "host": host,
            "event_time": event_time,
            "normalized": {
                "event_category": "authentication",
                "action": "ssh_login",
                "outcome": "failure",
                "user": iu.group("user"),
                "src_ip": iu.group("ip"),
                "protocol": "ssh",
                "process_name": "sshd",
                "message": message,
            },
        }

    cc = _CONN_CLOSED.search(message)
    if cc:
        return {
            "host": host,
            "event_time": event_time,
            "normalized": {
                "event_category": "network",
                "action": "connection_closed",
                "src_ip": cc.group("ip"),
                "protocol": "ssh",
                "process_name": "sshd",
                "message": message,
            },
        }

    return {
        "host": host,
        "event_time": event_time,
        "normalized": {"message": message, "process_name": "sshd"},
    }
