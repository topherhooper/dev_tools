#!/usr/bin/env bash
# Set up Glances on a Linux PC so Home Assistant can monitor it.
#
#   ./install-linux.sh <home-assistant-ip>
#
# Installs Glances into ~/glances-venv (no root, works on image-based distros),
# runs it as a systemd user service on port 61208 that starts at boot, and opens
# that port to the Home Assistant address only (firewalld or ufw, with sudo).
set -euo pipefail

HA_IP="${1:?usage: $0 <home-assistant-ip>}"
PORT="${GLANCES_PORT:-61208}"
VENV="$HOME/glances-venv"

python3 -m venv "$VENV"
"$VENV/bin/pip" install --quiet --upgrade pip
"$VENV/bin/pip" install --quiet "glances[web]"

mkdir -p "$HOME/.config/systemd/user"
cat > "$HOME/.config/systemd/user/glances.service" <<UNIT
[Unit]
Description=Glances web server (read by Home Assistant)
After=network-online.target

[Service]
ExecStart=$VENV/bin/glances -w --disable-webui -B 0.0.0.0 -p $PORT
Restart=on-failure

[Install]
WantedBy=default.target
UNIT

systemctl --user daemon-reload
systemctl --user enable --now glances.service
# Start at boot, before anyone logs in.
sudo loginctl enable-linger "$USER"

if command -v firewall-cmd >/dev/null 2>&1; then
  rule="rule family=\"ipv4\" source address=\"$HA_IP\" port port=\"$PORT\" protocol=\"tcp\" accept"
  sudo firewall-cmd --permanent --add-rich-rule="$rule"
  sudo firewall-cmd --reload
elif command -v ufw >/dev/null 2>&1; then
  sudo ufw allow from "$HA_IP" to any port "$PORT" proto tcp
else
  echo "No firewalld or ufw found; if a firewall is running, allow TCP $PORT from $HA_IP."
fi

sleep 3
if curl -fsS "http://localhost:$PORT/api/4/status" >/dev/null; then
  echo "Glances is answering on port $PORT. Add it in Home Assistant with this machine's address."
else
  echo "Glances is not answering yet; check: journalctl --user -u glances.service" >&2
  exit 1
fi
