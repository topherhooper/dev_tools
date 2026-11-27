#!/usr/bin/env bash
# Set up the network watcher on a Mac so it reports to Home Assistant.
#
#   ./install-macos.sh http://<home-assistant>:8123/api/webhook/<id> ["Display name"]
#
# No sudo needed: it runs as a launchd agent for your user, opens no port, and keeps
# everything under ~/.config/netwatch. Without root, macOS only lets it see your own
# programs' connections, not system services.
#
# To remove it:
#   launchctl bootout gui/$(id -u)/local.netwatch
#   rm -r ~/.config/netwatch ~/Library/LaunchAgents/local.netwatch.plist
set -euo pipefail

url=${1:?usage: install-macos.sh <webhook-url> [name]}
name=${2:-$(scutil --get ComputerName 2>/dev/null || hostname)}
dir=$HOME/.config/netwatch
plist=$HOME/Library/LaunchAgents/local.netwatch.plist
here=$(cd "$(dirname "$0")" && pwd)

mkdir -p "$dir" "$HOME/Library/LaunchAgents"
cp "$here/netwatch.py" "$dir/netwatch.py"
python3 -m venv "$dir/venv"
"$dir/venv/bin/pip" install --quiet --upgrade psutil
python3 - "$dir/config.json" "$url" "$name" <<'PY'
import json, sys
json.dump({"url": sys.argv[2], "name": sys.argv[3]}, open(sys.argv[1], "w"))
PY
chmod 600 "$dir/config.json"

cat > "$plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>local.netwatch</string>
  <key>ProgramArguments</key>
  <array><string>$dir/venv/bin/python</string><string>$dir/netwatch.py</string></array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardErrorPath</key><string>$dir/error.log</string>
</dict>
</plist>
PLIST

launchctl bootout "gui/$(id -u)/local.netwatch" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$plist"
echo "Network watch is installed and running. It learns quietly for 3 days, then reports new programs."
