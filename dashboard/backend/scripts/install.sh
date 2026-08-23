#!/bin/bash
# CySIEM Agent Installation Script (Linux)
# Installs the agent as a systemd service running backend/agent/main.py,
# downloaded live from the CySIEM server so it can never drift out of sync
# with the source in this repo.

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

# Requirement: validate root/sudo permissions up front, not partway through.
if [ "$(id -u)" -ne 0 ]; then
  echo "ERROR: This installer must run as root. Re-run with: sudo bash -s -- --token ... --server ... --agent-id ..."
  exit 1
fi

echo "--- CySIEM Agent Installation ---"

INSTALL_DIR="/opt/cysiem-agent"
mkdir -p "$INSTALL_DIR"

# Idempotent re-run: if this agent was already installed, stop the running
# service before overwriting its files so we don't have an old process and
# a new one racing on the same config.json.
if systemctl list-unit-files 2>/dev/null | grep -q "^cysiem-agent.service"; then
  echo "Existing cysiem-agent service found - stopping it before reinstalling."
  systemctl stop cysiem-agent 2>/dev/null || true
fi

# Quick reachability check before doing anything else, so the failure
# message is obvious instead of a generic timeout deep into the install.
echo "Checking connectivity to $SERVER..."
if ! curl -fsS --max-time 5 "$SERVER/" > /dev/null; then
  echo "ERROR: Cannot reach $SERVER from this machine."
  echo "  - Is the CySIEM backend running?"
  echo "  - Is SERVER_URL in backend/.env set to a reachable address (not 127.0.0.1) if this is a different machine?"
  echo "  - Is a firewall blocking port 8000?"
  exit 1
fi

# Download the real agent source - not a hand-copied duplicate.
echo "Downloading agent components from $SERVER..."
for f in main.py registration.py heartbeat.py collector.py receiver.py sysinfo.py config_loader.py; do
  sudo curl -fsSL "$SERVER/agent-files/$f" -o "$INSTALL_DIR/$f"
done

# Config file the agent code reads at startup.
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
if command -v apt-get >/dev/null 2>&1; then
  sudo apt-get update -y
  sudo apt-get install -y python3-pip python3-venv
elif command -v yum >/dev/null 2>&1; then
  sudo yum install -y python3-pip
fi

sudo python3 -m venv "$INSTALL_DIR/venv"
sudo "$INSTALL_DIR/venv/bin/pip" install --quiet requests psutil

echo "Registering agent and doing a first connectivity test..."
# cd into the install dir first as defense-in-depth - registration.py
# itself now resolves config.json via its own script location regardless
# of the caller's working directory, but this keeps behavior obvious.
if ! (cd "$INSTALL_DIR" && sudo "$INSTALL_DIR/venv/bin/python3" "$INSTALL_DIR/registration.py"); then
  echo "ERROR: Registration failed. Not installing the service - fix the error above and re-run this command."
  echo "This command is safe to re-run (it will reuse the same install directory and reconnect)."
  exit 1
fi

# systemd service runs main.py, which itself registers, then runs the
# heartbeat and log collector concurrently. If either stops, main.py exits
# and systemd restarts the whole thing (Restart=always).
cat <<EOF | sudo tee /etc/systemd/system/cysiem-agent.service > /dev/null
[Unit]
Description=CySIEM Security Agent
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/python3 $INSTALL_DIR/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "Starting CySIEM Agent service..."
sudo systemctl daemon-reload
sudo systemctl enable cysiem-agent
sudo systemctl restart cysiem-agent

sleep 2
if sudo systemctl is-active --quiet cysiem-agent; then
  echo "--- Installation Complete: agent service is running ---"
  echo "Check status with: sudo systemctl status cysiem-agent"
  echo "Check logs with:   sudo journalctl -u cysiem-agent -f"
else
  echo "--- Installation finished but the service is NOT running ---"
  echo "Run: sudo journalctl -u cysiem-agent -n 50 --no-pager"
  exit 1
fi
