#!/usr/bin/env bash
# Set up Glances on a Mac so Home Assistant can monitor it.
#
#   ./install-macos.sh
#
# Installs Glances into ~/glances-venv and runs it as a launchd agent on port
# 61208 whenever you are logged in. macOS may ask to install the developer
# tools the first time python3 runs, and to allow incoming connections.
set -euo pipefail

PORT="${GLANCES_PORT:-61208}"
VENV="$HOME/glances-venv"
PLIST="$HOME/Library/LaunchAgents/local.glances.plist"

python3 -m venv "$VENV"
"$VENV/bin/pip" install --quiet --upgrade pip
"$VENV/bin/pip" install --quiet "glances[web]"

mkdir -p "$(dirname "$PLIST")"
cat > "$PLIST" <<PL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>local.glances</string>
  <key>ProgramArguments</key><array>
    <string>$VENV/bin/glances</string>
    <string>-w</string><string>--disable-webui</string>
    <string>-B</string><string>0.0.0.0</string>
    <string>-p</string><string>$PORT</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
</dict></plist>
PL

launchctl unload "$PLIST" 2>/dev/null || true
launchctl load -w "$PLIST"

sleep 3
if curl -fsS "http://localhost:$PORT/api/4/status" >/dev/null; then
  echo "Glances is answering on port $PORT. Add it in Home Assistant with this Mac's address."
else
  echo "Glances is not answering yet; run $VENV/bin/glances -w to see why." >&2
  exit 1
fi
