"""Settings from env vars, with an optional .env file in the project root (home_assistant/)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def find_project_root(start: Path | None = None) -> Path:
    """Nearest ancestor of `start` (default: cwd) holding config/configuration.yaml."""
    start = (start or Path.cwd()).resolve()
    for candidate in (start, *start.parents):
        if (candidate / "config" / "configuration.yaml").is_file():
            return candidate
    return Path(__file__).resolve().parents[2]  # editable install fallback


PROJECT_ROOT = find_project_root()
CONFIG_DIR = PROJECT_ROOT / "config"

# The HA config dir is owned by root, but add-on SSH logs in as an unprivileged user
# (`hassio` on HA OS), so the remote rsync has to be elevated to write into it.
# Set HA_RSYNC_PATH="" for a host where the SSH user already owns the config dir.
DEFAULT_RSYNC_PATH = "sudo rsync"

# Where HA OS writes its backups, and where this machine keeps the copies it pulls.
DEFAULT_BACKUP_DIR = "/backup"
DEFAULT_LOCAL_BACKUP_DIR = Path.home() / "backups" / "home-assistant"


def load_dotenv(path: Path) -> None:
    """Minimal .env loader: KEY=VALUE lines; real env vars take precedence."""
    if not path.is_file():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


@dataclass(frozen=True)
class Settings:
    url: str
    token: str
    ssh: str
    remote_config_dir: str
    rsync_path: str
    remote_backup_dir: str
    local_backup_dir: Path

    @classmethod
    def from_env(cls, dotenv: Path | None = PROJECT_ROOT / ".env") -> Settings:
        if dotenv is not None:
            load_dotenv(dotenv)
        local_backups = os.environ.get("HA_BACKUP_LOCAL", "")
        return cls(
            url=os.environ.get("HA_URL", ""),
            token=os.environ.get("HA_TOKEN", ""),
            ssh=os.environ.get("HA_SSH", ""),
            remote_config_dir=os.environ.get("HA_CONFIG_DIR", "/config"),
            rsync_path=os.environ.get("HA_RSYNC_PATH", DEFAULT_RSYNC_PATH),
            remote_backup_dir=os.environ.get("HA_BACKUP_DIR", DEFAULT_BACKUP_DIR),
            local_backup_dir=(
                Path(local_backups).expanduser() if local_backups else DEFAULT_LOCAL_BACKUP_DIR
            ),
        )
