#!/bin/bash
# CySIEM Agent Installation Script (macOS)
# Installs the agent as a LaunchDaemon running backend/agent/main.py,
# downloaded live from the CySIEM server.

set -e

TOKEN=""
SERVER=""
AGENT_ID=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --token) TOKEN="$2"; shift 2 ;;
    --server) SERVER="$2"; shift 2 ;;
    --agent-id) AGENT_ID="$2"; shift 2 ;;
    *) shift ;;
  esac
done

if [ -z "$TOKEN" ] || [ -z "$SERVER" ] || [ -z "$AGENT_ID" ]; then
  echo "Error: Missing required parameters (--token, --server, --agent-id)"
  exit 1
fi

echo "--- CySIEM Agent Installation (macOS) ---"

INSTALL_DIR="/Library/Application Support/CySIEM/Agent"
sudo mkdir -p "$INSTALL_DIR"

echo "Checking connectivity to $SERVER..."
if ! curl -fsS --max-time 5 "$SERVER/" > /dev/null; then
  echo "ERROR: Cannot reach $SERVER from this machine. Check the backend is running and SERVER_URL is reachable."
  exit 1
fi

echo "Downloading agent components from $SERVER..."
for f in main.py registration.py heartbeat.py collector.py receiver.py sysinfo.py config_loader.py; do
  sudo curl -fsSL "$SERVER/agent-files/$f" -o "$INSTALL_DIR/$f"
done

cat <<EOF | sudo tee "$INSTALL_DIR/config.json" > /dev/null
{
  "server_url": "$SERVER",
  "token": "$TOKEN",
  "agent_id": $AGENT_ID,
  "heartbeat_interval": 5,
  "log_interval": 10,
  "version": "1.0.0"
}
EOF

echo "Installing dependencies..."
PYTHON3=$(command -v python3 || true)
if [ -z "$PYTHON3" ]; then
  echo "ERROR: python3 not found. Install Python 3 (e.g. via 'brew install python3') and re-run."
  exit 1
fi
sudo "$PYTHON3" -m pip install --quiet requests psutil

echo "Registering agent..."
if ! (cd "$INSTALL_DIR" && sudo "$PYTHON3" registration.py); then
  echo "ERROR: Registration failed. Not installing the LaunchDaemon - fix the error above and re-run."
  exit 1
fi

cat <<EOF | sudo tee /Library/LaunchDaemons/com.cysiem.agent.plist > /dev/null
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.cysiem.agent</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON3</string>
        <string>$INSTALL_DIR/main.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$INSTALL_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/var/log/cysiem-agent.log</string>
    <key>StandardErrorPath</key>
    <string>/var/log/cysiem-agent.err.log</string>
</dict>
</plist>
EOF

echo "Starting CySIEM Agent..."
sudo launchctl unload /Library/LaunchDaemons/com.cysiem.agent.plist 2>/dev/null || true
sudo launchctl load /Library/LaunchDaemons/com.cysiem.agent.plist

sleep 2
if sudo launchctl list | grep -q com.cysiem.agent; then
  echo "--- Installation Complete: agent is running ---"
  echo "Check logs with: tail -f /var/log/cysiem-agent.log"
else
  echo "--- Installation finished but the agent does not appear in launchctl list ---"
  echo "Check: cat /var/log/cysiem-agent.err.log"
  exit 1
fi
