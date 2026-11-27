# Home Assistant

Config-as-code for my Home Assistant install, plus `hactl`, a small Python CLI
for the HA API and for syncing config to and from the HA host.

```
home_assistant/
├── config/               # mirrors HA's /config directory
│   ├── configuration.yaml
│   ├── automations.yaml  # UI-managed (edited in HA, pulled back with `hactl pull`)
│   ├── scripts.yaml      # UI-managed
│   ├── scenes.yaml       # UI-managed
│   ├── packages/         # hand-written features, one file per area/feature
│   ├── custom_templates/ # Jinja macros shared by packages (see Alerts)
│   ├── dashboards/       # dashboards in YAML mode (see Dashboards)
│   └── secrets.example.yaml
├── src/hactl/            # CLI + API client
└── tests/
```

## Setup

```sh
cd home_assistant
make install                      # creates .venv with hactl + dev tools
cp .env.example .env              # fill in HA_URL, HA_TOKEN, HA_SSH
cp config/secrets.example.yaml config/secrets.yaml   # real values; git-ignored
.venv/bin/hactl ping
```

Create the token in HA under **Profile → Security → Long-lived access tokens**.

## Workflow

1. Edit YAML under `config/` (prefer new files in `config/packages/`).
2. `make lint test`, plus `make check-config` if a container engine is available
   (podman by default; `make check-config CONTAINER=docker` for docker). The HA config
   check also runs in CI on every PR that touches `home_assistant/`.
3. Deploy with `make deploy`, which runs `hactl deploy --dry-run` and then `hactl deploy`.
   This rsyncs `config/` to the host, has HA validate it, and reloads
   (`make deploy ARGS=--restart` for a full restart).
4. If you edited automations, scripts or scenes in the HA UI, run `hactl pull` and commit the diff.

Deploy never deletes files on the host and never copies `secrets.yaml`
(pass `--include-secrets` to do that), `.storage/` or the database.

## `hactl` commands

| Command | What it does |
| --- | --- |
| `hactl ping` | Check connectivity and show the HA version |
| `hactl states [--domain light] [--unavailable] [--json]` | List entity states |
| `hactl call light.turn_on --data '{"entity_id": "light.kitchen"}'` | Call a service |
| `hactl check` | Validate the config on the host |
| `hactl reload [--restart]` | Check, then reload all YAML (or restart) |
| `hactl deploy [--dry-run] [--no-reload] [--restart] [--include-secrets]` | Push `config/` to the host |
| `hactl pull [--dry-run]` | Fetch UI-edited automations, scripts and scenes |
| `hactl backups pull [--dry-run] [--stale-after HOURS]` | Copy HA's backups off the host and keep them here |

## Backups

Only `config/` is in git. `.storage` (entities, areas, dashboards, the Matter fabric),
`secrets.yaml`, HACS and `custom_components/` are not, and none of it is reconstructable
from this repo — so the backups are the real safety net, not the git history.

HA OS runs off eMMC/SD, and its only backup agent (`hassio.local`) writes to that same
card. Two layers, so a copy survives the card:

1. **HA creates one weekly**, Sunday at 04:15, to `hassio.local`, database and all add-ons
   included, keeping 3 copies (about three weeks). Configured under Settings → System →
   Backups. `sensor.house_alerts` warns when the newest is over 8 days old.
2. **Another machine pulls them off** with `hactl backups pull`, into
   `~/backups/home-assistant` (override with `HA_BACKUP_LOCAL`).

The pull never deletes. HA prunes the host to 3 copies; the local side keeps every backup
it has ever seen, which is the whole point of the second layer. It also exits non-zero
when the newest backup is older than `--stale-after` (default 48h; pass 192 for the weekly
schedule) — a schedule that quietly stops is the failure that actually happens, and this
makes it loud.

The pull currently runs on the Windows desktop, from the Ubuntu (WSL) clone at
`~/projects/dev_tools`, into `D:\Backups\home-assistant`. A Task Scheduler task named
"Home Assistant backup pull" starts it every Sunday at 10:00, or at the next logon if the
PC was off, and appends to `pull.log` in that folder:

```
wsl.exe -d Ubuntu -- bash -lc "cd ~/projects/dev_tools/home_assistant && .venv/bin/hactl backups pull --stale-after 192 >> /mnt/d/Backups/home-assistant/pull.log 2>&1"
```

On a Linux box, the units in `systemd/` do the same job (they run daily, which is harmless
with a weekly backup):

```sh
ln -s "$PWD"/systemd/hactl-backup-pull.{service,timer} ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now hactl-backup-pull.timer
systemctl --user list-timers hactl-backup-pull.timer
```

They assume this repo is at `~/projects/dev_tools`. The timer needs
`loginctl enable-linger "$USER"` to run while you are not logged in.

Backups are unencrypted, so the tars contain `secrets.yaml` and long-lived tokens in the
clear. Keep the folder they land in out of anything that syncs to the cloud.

Both copies are in the same house, which covers a dead SD card but not fire or theft. An
off-site leg is still missing. HA's built-in Google Drive location was tried and set aside
(it needs your own Google Cloud OAuth client); its OneDrive location, or Home Assistant
Cloud, are the simpler routes, and either wants backup encryption switched on first.

## Dashboards

Home is edited in the HA UI and lives in `.storage`, so only the backups hold it.
Monitoring Hub is in YAML mode: `config/dashboards/monitoring-hub.yaml`, registered under
`lovelace:` in `configuration.yaml`. Edit the file, deploy, then pick **Refresh** from the
dashboard's menu; the UI editor is disabled for it. Utilities is deliberately not here:
its charts hardcode the household's utility usage and this repo is public.

Adding a YAML dashboard under a URL that a UI-managed one already uses needs a restart,
after which the YAML one wins and HA logs that the stored one could not be registered.
Delete the stored copy under Settings → Dashboards once the YAML one looks right.

## Computers

`config/packages/computers.yaml` watches the household PCs: online or offline, CPU, memory,
fullest disk and hottest temperature sensor, shown in the Computers section of the Monitoring Hub.
Alerts (always-on machine offline 15 min, disk at 90%/97%, memory at 95%, anything over 90 °C)
go through the existing House Alerts notification.

To add a machine:

1. On the computer, run the setup script for its system from `scripts/glances/`. Each installs
   Glances, starts it at login or boot as a web server on port 61208, and (Windows and Linux)
   opens that port to the Home Assistant address only:
   - Windows, in an administrator PowerShell: `.\install-windows.ps1 -HomeAssistantIp <address>`
   - Linux: `./install-linux.sh <address>`
   - macOS: `./install-macos.sh`
2. In Home Assistant: Settings > Devices & services > Add integration > Glances, with the
   computer's address and port 61208.
3. Open the new device and give it the label `computer`. Add `computer_always_on` as well if it
   should alert when it goes offline; leave that off for machines that sleep or get shut down.

A computer nothing can be installed on, such as a work laptop, is monitored from the network
instead: add it with the Ping integration (Add integration > Ping, its address) and give that
device the `computer` label. It shows online or offline only, marked "network only", and a
sleeping laptop reads as offline. Reserve each address in the router, since Ping follows an
address rather than a machine.

No hostnames or addresses are kept in this repo; the labels decide what is monitored.
Thresholds are in `config/custom_templates/computers.jinja`.

## Network watch

A watcher of our own for "is something on this computer using the network that was not
before?". `scripts/netwatch/netwatch.py` runs on each computer as the logged-in user and
posts a report to a Home Assistant webhook every five minutes; `packages/network_watch.yaml`
keeps the latest report per computer in `sensor.network_watch`. Its only dependency is
`psutil`. It never blocks anything and opens no port.

It reports, per computer:

- a program newly holding a connection to a public internet address;
- a program newly accepting connections from other machines;
- a program doing either from a temp or downloads folder, where droppers usually start;
- on Windows, Microsoft Defender's status: real-time protection off, definitions more than
  a week old, or detections in the last 7 days.

For its first 3 days on a computer it learns what is normal without alerting (except the
temp-folder rule). After that a new program raises one House Alert, stays on the Network
watch card for a day, and then counts as known. Programs are told apart by path with version
numbers removed, so an app updating itself is not news.

What it is not: an antivirus. It has no list of known spyware, sees only the computers it is
installed on (no phones, smart devices or work laptops), samples every 20 seconds so a very
short connection can slip by, and anything with administrator rights can hide from it or
stop it. Without administrator or root rights it names only programs it is allowed to see;
on macOS and Linux that means your own, not system services.

Setup, once:

1. Add `netwatch_webhook_id: <long random string>` to `secrets.yaml` on the Home Assistant
   host **before** deploying, or the config will not load.
2. On each computer run the installer from `scripts/netwatch/` with the webhook address
   `http://<home-assistant>:8123/api/webhook/<that string>`:
   `install-windows.ps1 -WebhookUrl <address>`, `install-linux.sh <address>` or
   `install-macos.sh <address>`.

`python netwatch.py --once --print` shows what a computer would report without sending it.
A computer that stops reporting for 30 days drops off the card.

## Getting config onto the host

- **Any install type (default):** `hactl deploy` uses rsync over SSH. It needs `rsync` on
  both ends. On HA OS, install the *Advanced SSH & Web Terminal* add-on and add `rsync`
  to its packages.
- **HA OS alternative:** the *Git pull* add-on can pull this repo directly. HA expects
  the repo root to be `/config`, though, and this config lives in `home_assistant/config/`.
  To use it, split the config into its own repo or add a sync step.
