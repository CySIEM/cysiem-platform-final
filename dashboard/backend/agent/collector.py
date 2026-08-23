import os
import time
import re
import json
import platform
import subprocess
import threading
import shutil
import requests
import psutil
from config_loader import load_config

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG_PATH = os.path.join(_SCRIPT_DIR, "config.json")

# ============================================================================
# Shared: process-creation severity heuristics
# Small starter rule sets, not a real detection engine (Layer 4 - Detection
# Fabric - is where real scoring belongs). This just avoids calling every
# process INFO. Kept OS-agnostic where the pattern is genuinely OS-agnostic
# (e.g. curl/wget piped to a shell can happen via WSL/Git-Bash on Windows
# too), plus a Windows-specific set for well-known living-off-the-land
# techniques that have no Linux equivalent.
# ============================================================================
SUSPICIOUS_PROCESS_PATTERNS = [
    (re.compile(r'\bnc\b|\bncat\b|\bnetcat\b'), "MEDIUM", "Possible reverse/bind shell tool", "T1059"),
    (re.compile(r'\bwget\b|\bcurl\b.*(\|\s*sh|\|\s*bash)'), "HIGH", "Download piped directly into a shell", "T1105"),
    (re.compile(r'/bin/(ba)?sh\s+-i'), "HIGH", "Interactive shell spawned (possible reverse shell)", "T1059.004"),
    (re.compile(r'\bchmod\s+\+x\b'), "MEDIUM", "File made executable", "T1222"),
    (re.compile(r'\bsudo\s+su\b|\bsu\s+-'), "MEDIUM", "Privilege escalation to another user", "T1548.003"),
]

WINDOWS_SUSPICIOUS_PATTERNS = [
    (re.compile(r'-enc(odedcommand)?\b', re.IGNORECASE), "HIGH", "Base64-encoded PowerShell command", "T1027"),
    (re.compile(r'\bIEX\b|Invoke-Expression', re.IGNORECASE), "HIGH", "Dynamic code execution via Invoke-Expression", "T1059.001"),
    (re.compile(r'\bmshta\b|certutil\b.*-urlcache|bitsadmin\b.*/transfer', re.IGNORECASE), "HIGH", "Living-off-the-land download/execute utility", "T1105"),
    (re.compile(r'-w(indowstyle)?\s+hidden|-nop\b', re.IGNORECASE), "MEDIUM", "Hidden-window PowerShell execution", "T1564.003"),
]


def _classify_command_line(cmdline, extra_patterns=None):
    """Returns (severity, mitre_technique_or_None) for a command line, INFO/None if nothing matches."""
    patterns = SUSPICIOUS_PROCESS_PATTERNS + (extra_patterns or [])
    for pattern, sev, _why, mitre in patterns:
        if pattern.search(cmdline):
            return sev, mitre
    return "INFO", None


# ============================================================================
# Linux: auth.log / journald + psutil process polling
# ============================================================================
AUTH_LOG_CANDIDATES = ["/var/log/auth.log", "/var/log/secure"]

# `identifier[pid]:` prefix - e.g. "sshd-session[7006]:" or "sudo[1234]:".
# Only attached to a line that ALSO matches a real event pattern below, so
# a daemon's own status line (e.g. "sshd[6655]: Server listening...") is
# never mistaken for an actual login attempt's PID.
PROCESS_PID_RE = re.compile(r'(?P<process>[\w.\-/]+)\[(?P<pid>\d+)\]:')

FAILED_PW_RE = re.compile(r'Failed password for (invalid user )?(?P<user>\S+) from (?P<ip>\S+)(?: port (?P<port>\d+))?')
ACCEPTED_RE = re.compile(r'Accepted (password|publickey) for (?P<user>\S+) from (?P<ip>\S+)(?: port (?P<port>\d+))?')
INVALID_USER_RE = re.compile(r'Invalid user (?P<user>\S+) from (?P<ip>\S+)')
PAM_AUTH_FAILURE_RE = re.compile(r'authentication failure;.*?rhost=(?P<ip>\S+)(?:\s+user=(?P<user>\S+))?')
SUDO_RE = re.compile(r'sudo:\s*(?P<user>\S+)\s*:.*COMMAND=(?P<cmd>.+)')
# Routine, read-only/informational sudo commands are a genuinely lower
# priority than an arbitrary privileged command - this is a deliberate,
# documented severity tier (see README "Severity mapping"), not a general
# downgrade. Anything NOT matching this whitelist still gets MEDIUM exactly
# as before, so existing MEDIUM behavior for real privileged actions is
# unchanged. sudo always logs COMMAND= with the full absolute path (e.g.
# "/usr/bin/systemctl status ssh", not "systemctl status ssh") - matched
# against the basename, not a prefix regex, so the path doesn't matter.
_ROUTINE_BINARIES_ANY_ARGS = {"journalctl", "cat", "less", "tail", "ls", "whoami", "id"}
_ROUTINE_SUBCOMMANDS = {
    "systemctl": {"status", "is-active"},
    "apt": {"update", "list", "search"},
    "apt-get": {"update"},
    "dpkg": {"-l"},
    "ufw": {"status"},
    "service": {"--status-all"},
}

def _classify_sudo(cmd):
    parts = cmd.strip().split()
    if not parts:
        return "MEDIUM"
    binary = parts[0].rsplit("/", 1)[-1]
    rest = parts[1:]
    if binary in _ROUTINE_BINARIES_ANY_ARGS:
        return "LOW"
    if binary in _ROUTINE_SUBCOMMANDS and rest and rest[0] in _ROUTINE_SUBCOMMANDS[binary]:
        return "LOW"
    return "MEDIUM"

SESSION_OPEN_RE = re.compile(r'session opened for user (?P<user>\S+)')
SESSION_CLOSE_RE = re.compile(r'session closed for user (?P<user>\S+)')


def _parse_auth_lines(lines):
    """Shared parser for both a tailed auth.log file and journald output."""
    events = []
    for line in lines:
        pid = process = None
        pm = PROCESS_PID_RE.search(line)
        if pm:
            process = pm.group('process')
            pid = int(pm.group('pid'))

        def base(level, source, category, message, mitre=None, ip=None, user=None):
            e = {"level": level, "source": source, "category": category, "message": message}
            if mitre: e["mitre_technique"] = mitre
            if ip: e["ip_address"] = ip
            if user: e["user"] = user
            if process: e["process"] = process
            if pid is not None: e["pid"] = pid
            return e

        m = FAILED_PW_RE.search(line)
        if m:
            events.append(base("HIGH", "Authentication Failure", "Authentication",
                                f"Failed login for user '{m.group('user')}' from {m.group('ip')}",
                                "T1110", m.group('ip'), m.group('user')))
            continue
        m = INVALID_USER_RE.search(line)
        if m:
            events.append(base("HIGH", "Authentication Failure", "Authentication",
                                f"Invalid user '{m.group('user')}' attempted login from {m.group('ip')}",
                                "T1110", m.group('ip'), m.group('user')))
            continue
        m = PAM_AUTH_FAILURE_RE.search(line)
        if m:
            user = m.group('user')
            events.append(base("HIGH", "Authentication Failure", "Authentication",
                                f"PAM authentication failure from {m.group('ip')}" + (f" for user '{user}'" if user else ""),
                                "T1110", m.group('ip'), user))
            continue
        m = ACCEPTED_RE.search(line)
        if m:
            events.append(base("INFO", "Authentication Success", "Authentication",
                                f"Successful login for user '{m.group('user')}' from {m.group('ip')}",
                                None, m.group('ip'), m.group('user')))
            continue
        m = SUDO_RE.search(line)
        if m:
            cmd = m.group('cmd').strip()
            events.append(base(_classify_sudo(cmd), "Privilege Change", "PrivilegeChange",
                                f"User '{m.group('user')}' ran with sudo: {cmd}",
                                "T1548.003", None, m.group('user')))
            continue
        m = SESSION_OPEN_RE.search(line)
        if m:
            events.append(base("INFO", "Session Opened", "Session",
                                f"Session opened for user '{m.group('user')}'", None, None, m.group('user')))
            continue
        m = SESSION_CLOSE_RE.search(line)
        if m:
            events.append(base("INFO", "Session Closed", "Session",
                                f"Session closed for user '{m.group('user')}'", None, None, m.group('user')))
    return events


class _LinuxAuthSource:
    def __init__(self):
        self.file_path = next((p for p in AUTH_LOG_CANDIDATES if os.path.exists(p)), None)
        self._file_offset = 0
        self._journalctl_available = shutil.which("journalctl") is not None
        self._journal_cursor = None
        self._warned = False

    def read_new_lines(self):
        if self.file_path:
            return self._read_file()
        if self._journalctl_available:
            return self._read_journald()
        if not self._warned:
            self._warned = True
            return [f"__WARN__ No auth log file found ({AUTH_LOG_CANDIDATES}) and journalctl is not available. "
                    f"Authentication events will not be collected on this host."]
        return []

    def _read_file(self):
        try:
            with open(self.file_path, 'r', errors='ignore') as f:
                f.seek(self._file_offset)
                lines = f.readlines()
                self._file_offset = f.tell()
            return lines
        except PermissionError:
            if not self._warned:
                self._warned = True
                return [f"__WARN__ Permission denied reading {self.file_path}. "
                        f"Agent likely isn't running as root - authentication events won't be collected."]
            return []

    def _read_journald(self):
        cursor_cmd = ["journalctl", "-q", "--no-pager", "-o", "cat", "--show-cursor"]
        if self._journal_cursor:
            cursor_cmd += ["--after-cursor", self._journal_cursor]
        else:
            cursor_cmd += ["--since", "-1min"]
        try:
            out = subprocess.run(cursor_cmd, capture_output=True, text=True, timeout=5)
            lines = out.stdout.splitlines()
        except Exception:
            return []

        content_lines = []
        for line in lines:
            if line.startswith("-- cursor:"):
                self._journal_cursor = line.split("cursor:", 1)[1].strip()
            else:
                content_lines.append(line)
        return content_lines


def _scan_new_processes(known_pids_ref):
    """Real psutil-based process-creation detection, OS-agnostic (works on Linux, Windows, macOS alike)."""
    events = []
    current_pids = set(psutil.pids())
    new_pids = current_pids - known_pids_ref[0]
    known_pids_ref[0] = current_pids

    for pid in new_pids:
        try:
            p = psutil.Process(pid)
            name = p.name()
            cmdline = " ".join(p.cmdline()) or name
            username = p.username()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

        extra = WINDOWS_SUSPICIOUS_PATTERNS if platform.system() == "Windows" else None
        severity, mitre = _classify_command_line(cmdline, extra)

        message = f"New process: {name} (pid {pid}) by {username}"
        entry = {
            "level": severity, "source": "Process Monitor", "category": "Process Creation",
            "user": username, "process": name, "pid": pid, "command_line": cmdline, "message": message,
        }
        if mitre:
            entry["mitre_technique"] = mitre
        events.append(entry)
    return events


# ============================================================================
# Windows: Security Event Log (4624 logon success, 4625 logon failure,
# 4688 process creation) via Get-WinEvent - avoids adding a pywin32
# dependency to the installer, using only what's already required
# (PowerShell, present on every supported Windows version).
# ============================================================================

# Queries the Security log for events since $StartTime, extracts the
# EventData fields we care about via each event's own XML (the only
# reliable way to get named fields out of Get-WinEvent), and emits a
# flat JSON array - always an array (@(...)), even for zero or one
# result, so the Python side never has to guess whether it got a list
# or a bare object back.
_PS_EVENT_QUERY_TEMPLATE = r'''
$ErrorActionPreference = "SilentlyContinue"
$events = @(Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4624,4625,4688; StartTime='%s'} -ErrorAction SilentlyContinue)
$results = @()
foreach ($e in $events) {
    try {
        $xml = [xml]$e.ToXml()
        $data = @{}
        foreach ($d in $xml.Event.EventData.Data) {
            if ($d.Name) { $data[$d.Name] = $d.'#text' }
        }
        $results += [PSCustomObject]@{
            TimeCreated = $e.TimeCreated.ToUniversalTime().ToString("o")
            Id = $e.Id
            RecordId = $e.RecordId
            SubjectUserName = $data.SubjectUserName
            TargetUserName = $data.TargetUserName
            IpAddress = $data.IpAddress
            NewProcessId = $data.NewProcessId
            NewProcessName = $data.NewProcessName
            ParentProcessName = $data.ParentProcessName
            CommandLine = $data.CommandLine
            LogonType = $data.LogonType
            FailureReason = $data.FailureReason
        }
    } catch { }
}
@($results) | ConvertTo-Json -Depth 4 -Compress
'''.strip()


class _WindowsEventSource:
    def __init__(self):
        self._last_start = None  # ISO string; None on first call = look back 1 minute
        self._seen_record_ids = set()
        self._warned = False

    def read_new_events(self):
        """Returns a list of raw dicts (one per Security-log event), or [] if none/unavailable."""
        import datetime
        now = datetime.datetime.now(datetime.timezone.utc)
        start = self._last_start or (now - datetime.timedelta(minutes=1)).isoformat()
        self._last_start = now.isoformat()

        script = _PS_EVENT_QUERY_TEMPLATE % start
        try:
            proc = subprocess.run(
                ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
                capture_output=True, text=True, timeout=20
            )
        except FileNotFoundError:
            if not self._warned:
                self._warned = True
                return [{"__WARN__": "powershell.exe not found - cannot collect Windows Security events on this host."}]
            return []
        except subprocess.TimeoutExpired:
            return []

        out = (proc.stdout or "").strip()
        if not out:
            return []

        try:
            data = json.loads(out)
        except json.JSONDecodeError:
            # A malformed/partial response from PowerShell for this one cycle
            # is not worth crashing the collector over - just skip this pass.
            return []

        if isinstance(data, dict):
            data = [data]
        if not isinstance(data, list):
            return []

        # De-dupe by RecordId across polling cycles (StartTime boundaries can overlap slightly).
        fresh = []
        for evt in data:
            rid = evt.get("RecordId")
            if rid is not None:
                if rid in self._seen_record_ids:
                    continue
                self._seen_record_ids.add(rid)
            fresh.append(evt)

        # Keep the de-dupe set from growing forever.
        if len(self._seen_record_ids) > 5000:
            self._seen_record_ids = set(list(self._seen_record_ids)[-2000:])

        return fresh


def _normalize_windows_event(evt):
    """
    Maps a raw Get-WinEvent record to this project's event schema.
    PID is only ever populated from NewProcessId on a real 4688 event -
    never from a logon event's ProcessId, which belongs to the OS logon
    process (e.g. winlogon/lsass), not to "the event" the way the doc
    warned about conflating a listener's PID with a session's PID on Linux.
    """
    if "__WARN__" in evt:
        return {"level": "MEDIUM", "source": "Log Collector", "category": "System", "message": evt["__WARN__"]}

    event_id = evt.get("Id")
    ip = evt.get("IpAddress")
    if ip in ("-", "::1", None):
        ip = "127.0.0.1" if ip == "::1" else None

    if event_id == 4625:
        user = evt.get("TargetUserName") or "unknown"
        reason = evt.get("FailureReason")
        msg = f"Failed logon for user '{user}'" + (f" from {ip}" if ip else "")
        return {
            "level": "HIGH", "source": "Authentication Failure", "category": "Authentication",
            "event_id": "4625", "user": user, "ip_address": ip, "mitre_technique": "T1110",
            "message": msg + (f" ({reason})" if reason else ""),
        }
    if event_id == 4624:
        user = evt.get("TargetUserName") or "unknown"
        return {
            "level": "INFO", "source": "Authentication Success", "category": "Authentication",
            "event_id": "4624", "user": user, "ip_address": ip,
            "message": f"Successful logon for user '{user}'" + (f" from {ip}" if ip else ""),
        }
    if event_id == 4688:
        proc_name = evt.get("NewProcessName") or "unknown"
        # Trim to just the executable name for readability; full path stays in the message.
        short_name = proc_name.split("\\")[-1] if proc_name else "unknown"
        cmdline = evt.get("CommandLine") or ""
        pid = None
        raw_pid = evt.get("NewProcessId")
        if raw_pid:
            try:
                pid = int(raw_pid, 16) if str(raw_pid).lower().startswith("0x") else int(raw_pid)
            except (ValueError, TypeError):
                pid = None
        severity, mitre = _classify_command_line(cmdline or short_name, WINDOWS_SUSPICIOUS_PATTERNS)
        entry = {
            "level": severity, "source": "Process Monitor", "category": "Process Creation",
            "event_id": "4688", "user": evt.get("SubjectUserName"), "process": short_name,
            "message": f"New process: {short_name}" + (f" (pid {pid})" if pid else "") +
                       (f" by {evt.get('SubjectUserName')}" if evt.get('SubjectUserName') else ""),
        }
        if pid is not None:
            entry["pid"] = pid
        if cmdline:
            entry["command_line"] = cmdline
        if mitre:
            entry["mitre_technique"] = mitre
        return entry

    return None


# ============================================================================
# Collector
# ============================================================================
class CySiemCollector:
    def __init__(self, config_path=None):
        self.config = load_config(config_path or DEFAULT_CONFIG_PATH)
        self.server_url = self.config['server_url'].rstrip('/')
        self.agent_id = self.config['agent_id']
        self.token = self.config['token']
        self.interval = self.config.get('log_interval', 10)

        self._os = platform.system()  # "Linux", "Windows", "Darwin"
        self._linux_auth_source = _LinuxAuthSource() if self._os == "Linux" else None
        self._windows_event_source = _WindowsEventSource() if self._os == "Windows" else None

        # Process detection runs on its own tight loop in a background
        # thread (1s cadence) instead of once per send interval, so
        # shorter-lived activity has a real chance of being caught -
        # OS-agnostic, works the same on Linux and Windows via psutil.
        self._proc_buffer = []
        self._proc_lock = threading.Lock()
        self._known_pids = [set(psutil.pids())]  # boxed in a list so _scan_new_processes can mutate it
        self._stop = False

    def _process_scan_loop(self):
        while not self._stop:
            try:
                events = _scan_new_processes(self._known_pids)
                if events:
                    with self._proc_lock:
                        self._proc_buffer.extend(events)
            except Exception as e:
                print(f"Process scan error: {e}")
            time.sleep(1)

    def _drain_process_buffer(self):
        with self._proc_lock:
            logs, self._proc_buffer = self._proc_buffer, []
        return logs

    def _collect_linux(self):
        logs = self._drain_process_buffer()
        raw_lines = self._linux_auth_source.read_new_lines()
        text_lines = [l for l in raw_lines if not l.startswith("__WARN__")]
        for warn in [l for l in raw_lines if l.startswith("__WARN__")]:
            logs.append({"level": "MEDIUM", "source": "Log Collector", "category": "System",
                         "message": warn.replace("__WARN__ ", "")})
        logs.extend(_parse_auth_lines(text_lines))
        return logs

    def _collect_windows(self):
        # Real process-creation events also come from psutil here (same as
        # Linux/macOS) - the Windows Event Log query ADDS logon success/
        # failure telemetry (4624/4625) and a second, richer source of
        # process-creation data (4688, with parent process + command line)
        # on top of it, rather than replacing psutil detection.
        logs = self._drain_process_buffer()
        raw_events = self._windows_event_source.read_new_events()
        for evt in raw_events:
            normalized = _normalize_windows_event(evt)
            if normalized:
                logs.append(normalized)
        return logs

    def _collect_macos(self):
        # Not implemented yet - say so honestly rather than fabricating events.
        return [{
            "level": "MEDIUM", "source": "Log Collector", "category": "System",
            "message": "Real log collection for macOS is not implemented yet. Only heartbeat/metrics are active on this host.",
        }]

    def collect_logs(self):
        if self._os == "Linux":
            return self._collect_linux()
        if self._os == "Windows":
            return self._collect_windows()
        return self._collect_macos()

    def run(self):
        print(f"Starting CySIEM Log Collector for Agent {self.agent_id} ({self._os}) -> {self.server_url}")
        scan_thread = threading.Thread(target=self._process_scan_loop, daemon=True)
        scan_thread.start()

        while True:
            try:
                logs = self.collect_logs()
                if logs:
                    payload = {"agent_id": self.agent_id, "token": self.token, "logs": logs}
                    resp = requests.post(f"{self.server_url}/api/logs/ingest", json=payload, timeout=10)
                    if resp.status_code == 401:
                        print("Log ingest rejected: invalid/revoked token. Stopping collector.")
                        self._stop = True
                        return
            except requests.exceptions.ConnectionError as e:
                print(f"Collector could not reach server (will retry): {e}")
            except Exception as e:
                print(f"Collector error: {e}")
            time.sleep(self.interval)


if __name__ == "__main__":
    from config_loader import ConfigError
    try:
        collector = CySiemCollector()
    except ConfigError as e:
        print(f"Collector could not start: {e}")
        raise SystemExit(1)
    collector.run()
