"""Small standalone validators reused across schemas/services."""
import ipaddress
import re

_CVE_RE = re.compile(r"^CVE-\d{4}-\d{4,7}$", re.IGNORECASE)


def is_valid_ip(value: str) -> bool:
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def is_valid_cve(value: str) -> bool:
    return bool(_CVE_RE.match(value))
