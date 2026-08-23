"""Generates synthetic firewall/IDS/Sysmon/auth/DNS log lines for testing
the ingestion pipeline end-to-end without a live log source. Run with:
python -m scripts.generate_synthetic_logs > sample_logs.txt
"""
import random

_HOSTS = ["HOST-FIN01", "HOST-HR02", "HOST-DEV07", "SRV-DB01"]
_IPS = ["10.0.1.15", "10.0.2.22", "10.0.3.8", "185.220.101.5"]
_USERS = ["jdoe", "asmith", "rkumar", "admin"]

_TEMPLATES = [
    "firewall DENY SRC={ip} DST=10.0.0.1 DPT=443",
    "sshd: Failed password for user={user} from {ip}",
    "Sysmon EventID=1 Image=C:\\Windows\\System32\\powershell.exe user={user} on {host}",
    "alert signature='ET SCAN Possible Nmap' SRC={ip} classtype=attempted-recon",
    "dns query type=A name=malicious-c2.example resolved={ip} host={host}",
    "user={user} logon on {host} succeeded",
    "Host {host} exploited via CVE-2021-44228",
]


def generate(n: int = 50) -> list[str]:
    lines = []
    for _ in range(n):
        template = random.choice(_TEMPLATES)
        lines.append(
            template.format(
                ip=random.choice(_IPS), user=random.choice(_USERS), host=random.choice(_HOSTS)
            )
        )
    return lines


if __name__ == "__main__":
    for line in generate():
        print(line)
