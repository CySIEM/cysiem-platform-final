import os
import sys
import requests
from sysinfo import get_sys_info
from config_loader import load_config, ConfigError

# Resolve config.json relative to THIS script's own location, not the
# shell's current working directory. Running this via an absolute path
# (e.g. /opt/cysiem-agent/venv/bin/python /opt/cysiem-agent/registration.py)
# from some other directory - which is exactly what install.sh does before
# a working directory is established - used to fail with
# FileNotFoundError: [Errno 2] No such file or directory: 'config.json'
# because "config.json" was being looked up relative to wherever the
# installer script itself happened to be running from.
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG_PATH = os.path.join(_SCRIPT_DIR, "config.json")


def register_agent(server_url, agent_id, token):
    """
    First contact with the backend. Reuses the heartbeat endpoint (the
    backend treats "hostname was never set" as first contact and sets
    status to Connecting instead of Active - see api/heartbeat.py).
    """
    url = f"{server_url.rstrip('/')}/api/heartbeat/"
    payload = get_sys_info()
    payload["agent_id"] = agent_id
    payload["token"] = token

    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            return True, "Registered successfully."
        if response.status_code == 401:
            return False, "Registration rejected: invalid or revoked token."
        if response.status_code == 404:
            return False, "Registration rejected: agent ID not found on server (was it deleted?)."
        return False, f"Registration failed: HTTP {response.status_code} - {response.text}"
    except requests.exceptions.ConnectionError:
        return False, f"Could not reach server at {server_url}. Check SERVER_URL and network connectivity."
    except Exception as e:
        return False, f"Registration error: {e}"


if __name__ == "__main__":
    config_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CONFIG_PATH
    try:
        config = load_config(config_path)
    except ConfigError as e:
        print(f"Registration failed: {e}")
        raise SystemExit(1)

    ok, msg = register_agent(config["server_url"], config["agent_id"], config["token"])
    print(msg)
    if not ok:
        raise SystemExit(1)
