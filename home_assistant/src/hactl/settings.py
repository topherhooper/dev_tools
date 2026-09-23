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

    @classmethod
    def from_env(cls, dotenv: Path | None = PROJECT_ROOT / ".env") -> Settings:
        if dotenv is not None:
            load_dotenv(dotenv)
        return cls(
            url=os.environ.get("HA_URL", ""),
            token=os.environ.get("HA_TOKEN", ""),
            ssh=os.environ.get("HA_SSH", ""),
            remote_config_dir=os.environ.get("HA_CONFIG_DIR", "/config"),
        )
