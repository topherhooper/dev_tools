"""Move config between this repo and the HA host with rsync over SSH."""

from __future__ import annotations

import shutil
import subprocess
from collections.abc import Sequence
from pathlib import Path

from hactl.client import HAError
from hactl.settings import CONFIG_DIR, DEFAULT_RSYNC_PATH

# Never push these: they are either local-only or HA runtime state.
PUSH_EXCLUDES = (
    "secrets.yaml",
    "secrets.example.yaml",
    ".gitignore",
    ".storage/",
    ".cloud/",
    ".HA_VERSION",
    "*.db*",
    "*.log*",
    "__pycache__/",
)

# Files the HA UI editors write to; pull these back so UI edits land in git.
UI_MANAGED_FILES = ("automations.yaml", "scripts.yaml", "scenes.yaml")


def push_command(
    ssh: str,
    remote_dir: str,
    *,
    local_dir: Path = CONFIG_DIR,
    include_secrets: bool = False,
    dry_run: bool = False,
    rsync_path: str = DEFAULT_RSYNC_PATH,
) -> list[str]:
    # No --delete: removing a file in git should not silently wipe it on the host.
    cmd = ["rsync", "-rlptzv", "--checksum"]
    # Elevate only the far-side rsync; the SSH login itself stays unprivileged.
    if rsync_path:
        cmd += ["--rsync-path", rsync_path]
    if dry_run:
        cmd.append("--dry-run")
    for pattern in PUSH_EXCLUDES:
        if include_secrets and pattern == "secrets.yaml":
            continue
        cmd += ["--exclude", pattern]
    cmd += [f"{local_dir}/", f"{ssh}:{remote_dir.rstrip('/')}/"]
    return cmd


def pull_command(
    ssh: str,
    remote_dir: str,
    *,
    local_dir: Path = CONFIG_DIR,
    files: Sequence[str] = UI_MANAGED_FILES,
    dry_run: bool = False,
) -> list[str]:
    remote_dir = remote_dir.rstrip("/")
    cmd = ["rsync", "-tzv", "--checksum"]
    if dry_run:
        cmd.append("--dry-run")
    cmd += [f"{ssh}:{remote_dir}/{name}" for name in files]
    cmd.append(f"{local_dir}/")
    return cmd


def backup_pull_command(
    ssh: str,
    remote_dir: str,
    local_dir: Path,
    *,
    dry_run: bool = False,
    rsync_path: str = DEFAULT_RSYNC_PATH,
) -> list[str]:
    """Mirror HA's backup directory onto this machine.

    Backups are immutable, already-compressed tars, so this skips -z and --checksum and
    leans on --ignore-existing to make repeat runs nearly free. No --delete: HA prunes
    the host to its retention limit, and the whole point of the copy is to outlive that.
    """
    cmd = ["rsync", "-rlptv", "--ignore-existing"]
    # /backup and its contents are root-owned; the add-on SSH login is not.
    if rsync_path:
        cmd += ["--rsync-path", rsync_path]
    if dry_run:
        cmd.append("--dry-run")
    cmd += [f"{ssh}:{remote_dir.rstrip('/')}/", f"{local_dir}/"]
    return cmd


def run(cmd: list[str]) -> None:
    if shutil.which(cmd[0]) is None:
        raise HAError(f"{cmd[0]} not found; install it locally (and on the HA host)")
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True)
