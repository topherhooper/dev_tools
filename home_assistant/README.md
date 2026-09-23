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
2. `make lint test`, plus `make check-config` if Docker is available. The HA config
   check also runs in CI on every PR that touches `home_assistant/`.
3. Deploy with `.venv/bin/hactl deploy --dry-run`, then `hactl deploy`. This rsyncs
   `config/` to the host, has HA validate it, and reloads (`--restart` for a full restart).
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

## Getting config onto the host

- **Any install type (default):** `hactl deploy` uses rsync over SSH. It needs `rsync` on
  both ends. On HA OS, install the *Advanced SSH & Web Terminal* add-on and add `rsync`
  to its packages.
- **HA OS alternative:** the *Git pull* add-on can pull this repo directly. HA expects
  the repo root to be `/config`, though, and this config lives in `home_assistant/config/`.
  To use it, split the config into its own repo or add a sync step.
