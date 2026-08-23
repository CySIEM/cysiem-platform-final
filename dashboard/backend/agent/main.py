import os
import sys
import time
import threading

from registration import register_agent
from heartbeat import CySiemHeartbeat
from collector import CySiemCollector
from config_loader import load_config, ConfigError

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG_PATH = os.path.join(_SCRIPT_DIR, "config.json")


def register_with_retry(config, max_attempts=5):
    for attempt in range(1, max_attempts + 1):
        ok, msg = register_agent(config['server_url'], config['agent_id'], config['token'])
        print(f"[register attempt {attempt}/{max_attempts}] {msg}")
        if ok:
            return True
        if "invalid or revoked token" in msg.lower() or "agent id not found" in msg.lower():
            # Retrying won't fix a bad token/deleted agent - fail fast with a clear reason.
            return False
        time.sleep(min(5 * attempt, 30))
    return False


def main():
    try:
        config = load_config(DEFAULT_CONFIG_PATH)
    except ConfigError as e:
        print(f"Cannot start: {e}")
        sys.exit(1)

    if not register_with_retry(config):
        print("Registration failed after retries. Not starting heartbeat/collector.")
        print("Check: is SERVER_URL reachable from this machine, and is the token still valid "
              "(agent wasn't deleted/re-enrolled on the dashboard)?")
        sys.exit(1)

    heartbeat_thread = threading.Thread(target=CySiemHeartbeat(config_path=DEFAULT_CONFIG_PATH).run, daemon=True)
    collector_thread = threading.Thread(target=CySiemCollector(config_path=DEFAULT_CONFIG_PATH).run, daemon=True)

    heartbeat_thread.start()
    collector_thread.start()

    # Keep the process alive; systemd/launchd/Task Scheduler restarts us if we die.
    while True:
        if not heartbeat_thread.is_alive() or not collector_thread.is_alive():
            print("A worker thread stopped unexpectedly. Exiting so the service manager restarts us.")
            sys.exit(1)
        time.sleep(5)


if __name__ == "__main__":
    main()
