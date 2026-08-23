import os
import time
import requests
import psutil
from sysinfo import get_sys_info
from config_loader import load_config

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG_PATH = os.path.join(_SCRIPT_DIR, "config.json")


class CySiemHeartbeat:
    def __init__(self, config_path=None):
        # Same fix as registration.py: resolve config.json next to this
        # script by default (not the launch directory), and load it via
        # the shared BOM-tolerant loader instead of a bare json.load().
        self.config = load_config(config_path or DEFAULT_CONFIG_PATH)
        self.server_url = self.config['server_url'].rstrip('/')
        self.agent_id = self.config['agent_id']
        self.token = self.config['token']
        self.interval = self.config.get('heartbeat_interval', 5)
        self._boot_time = psutil.boot_time()
        self._last_net = psutil.net_io_counters()
        self._last_net_time = time.time()

    def _network_usage_mbps(self):
        """
        Real network throughput, not a random number: bytes sent+received
        since the last heartbeat, converted to Mbps.
        """
        now_counters = psutil.net_io_counters()
        now_time = time.time()
        elapsed = max(now_time - self._last_net_time, 1e-6)

        bytes_delta = (
            (now_counters.bytes_sent - self._last_net.bytes_sent) +
            (now_counters.bytes_recv - self._last_net.bytes_recv)
        )
        mbps = (bytes_delta * 8) / elapsed / 1_000_000

        self._last_net = now_counters
        self._last_net_time = now_time
        return round(max(mbps, 0), 2)

    def _format_uptime(self, seconds):
        seconds = int(seconds)
        days, seconds = divmod(seconds, 86400)
        hours, seconds = divmod(seconds, 3600)
        minutes, _ = divmod(seconds, 60)
        if days:
            return f"{days}d {hours}h {minutes}m"
        if hours:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"

    def collect_metrics(self):
        data = get_sys_info()
        data.update({
            "agent_id": self.agent_id,
            "token": self.token,
            "cpu_usage": psutil.cpu_percent(interval=1),
            "memory_usage": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "network_usage": self._network_usage_mbps(),
            "uptime": self._format_uptime(time.time() - self._boot_time),
        })
        return data

    def run(self):
        print(f"Starting CySIEM Heartbeat for Agent {self.agent_id} -> {self.server_url}")
        while True:
            try:
                metrics = self.collect_metrics()
                resp = requests.post(f"{self.server_url}/api/heartbeat/", json=metrics, timeout=10)
                if resp.status_code == 401:
                    print("Heartbeat rejected: invalid/revoked token. Agent needs re-enrollment. Stopping.")
                    return
                if resp.status_code == 404:
                    print("Heartbeat rejected: agent no longer exists on server. Stopping.")
                    return
                if resp.status_code != 200:
                    print(f"Heartbeat error: HTTP {resp.status_code} - {resp.text}")
            except requests.exceptions.ConnectionError as e:
                print(f"Heartbeat could not reach server: {e}")
            except Exception as e:
                print(f"Heartbeat error: {e}")
            time.sleep(self.interval)


if __name__ == "__main__":
    from config_loader import ConfigError
    try:
        hb = CySiemHeartbeat()
    except ConfigError as e:
        print(f"Heartbeat could not start: {e}")
        raise SystemExit(1)
    hb.run()
