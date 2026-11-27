#!/usr/bin/env bash
# Set up the network watcher on a Linux PC so it reports to Home Assistant.
#
#   ./install-linux.sh http://<home-assistant>:8123/api/webhook/<id> ["Display name"]
#
# No root needed: it runs as a systemd user service, opens no port, and keeps
# everything under ~/.config/netwatch (psutil goes into a private venv there, which
# also works on image-based systems such as Bazzite).
# Without root it can name only your own programs, not system services.
#
# To remove it: systemctl --user disable --now netwatch; rm -r ~/.config/netwatch
set -euo pipefail

url=${1:?usage: install-linux.sh <webhook-url> [name]}
name=${2:-$(hostname)}
dir=${XDG_CONFIG_HOME:-$HOME/.config}/netwatch
here=$(cd "$(dirname "$0")" && pwd)

mkdir -p "$dir" "$HOME/.config/systemd/user"
cp "$here/netwatch.py" "$dir/netwatch.py"
python3 -m venv "$dir/venv"
"$dir/venv/bin/pip" install --quiet --upgrade psutil
python3 - "$dir/config.json" "$url" "$name" <<'PY'
import json, sys
json.dump({"url": sys.argv[2], "name": sys.argv[3]}, open(sys.argv[1], "w"))
PY
chmod 600 "$dir/config.json"

cat > "$HOME/.config/systemd/user/netwatch.service" <<UNIT
[Unit]
Description=Network watch (reports to Home Assistant)
After=network-online.target

[Service]
ExecStart=$dir/venv/bin/python $dir/netwatch.py
Restart=on-failure
RestartSec=60

[Install]
WantedBy=default.target
UNIT

systemctl --user daemon-reload
systemctl --user enable --now netwatch.service
echo "Network watch is installed and running. It learns quietly for 3 days, then reports new programs."
