import os
from pathlib import Path

from hactl.settings import find_project_root, load_dotenv
from hactl.sync import backup_pull_command, pull_command, push_command

LOCAL = Path("/repo/config")


def test_push_excludes_secrets_by_default_and_never_deletes():
    cmd = push_command("root@ha", "/config/", local_dir=LOCAL)
    assert "--delete" not in cmd
    assert cmd[-2:] == ["/repo/config/", "root@ha:/config/"]
    excluded = [cmd[i + 1] for i, a in enumerate(cmd) if a == "--exclude"]
    assert "secrets.yaml" in excluded
    assert ".storage/" in excluded


def test_push_elevates_remote_rsync_by_default():
    cmd = push_command("hassio@ha", "/config", local_dir=LOCAL)
    assert cmd[cmd.index("--rsync-path") + 1] == "sudo rsync"


def test_push_rsync_path_can_be_disabled():
    cmd = push_command("root@ha", "/config", local_dir=LOCAL, rsync_path="")
    assert "--rsync-path" not in cmd


def test_pull_does_not_elevate():
    # Pulling only reads world-readable files, so it needs no elevation.
    cmd = pull_command("hassio@ha", "/config", local_dir=LOCAL)
    assert "--rsync-path" not in cmd


def test_push_include_secrets_and_dry_run():
    cmd = push_command("root@ha", "/config", local_dir=LOCAL, include_secrets=True, dry_run=True)
    excluded = [cmd[i + 1] for i, a in enumerate(cmd) if a == "--exclude"]
    assert "secrets.yaml" not in excluded
    assert "secrets.example.yaml" in excluded
    assert "--dry-run" in cmd


def test_pull_fetches_ui_managed_files():
    cmd = pull_command("root@ha", "/config/", local_dir=LOCAL)
    assert "root@ha:/config/automations.yaml" in cmd
    assert "root@ha:/config/scripts.yaml" in cmd
    assert cmd[-1] == "/repo/config/"


def test_backup_pull_never_deletes_and_skips_existing():
    # HA prunes the host to its retention limit; the copy here is meant to outlive that.
    cmd = backup_pull_command("hassio@ha", "/backup/", Path("/home/me/backups/ha"))
    assert "--delete" not in cmd
    assert "--ignore-existing" in cmd
    assert cmd[-2:] == ["hassio@ha:/backup/", "/home/me/backups/ha/"]


def test_backup_pull_elevates_remote_rsync_and_threads_dry_run():
    # /backup is root-owned, so the far-side rsync needs the same elevation deploy uses.
    cmd = backup_pull_command("hassio@ha", "/backup", Path("/b"), dry_run=True)
    assert cmd[cmd.index("--rsync-path") + 1] == "sudo rsync"
    assert "--dry-run" in cmd


def test_backup_pull_skips_compression_and_checksums():
    # Backup tars are immutable and already compressed; -z/--checksum would just burn CPU.
    cmd = backup_pull_command("hassio@ha", "/backup", Path("/b"))
    assert "--checksum" not in cmd
    assert cmd[1] == "-rlptv"


def test_load_dotenv_does_not_override_env(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("# comment\nHA_URL='http://x:8123'\nHA_TOKEN=from_file\n")
    monkeypatch.setenv("HA_URL", "")
    monkeypatch.delenv("HA_URL")
    monkeypatch.setenv("HA_TOKEN", "from_env")
    load_dotenv(env)
    assert os.environ["HA_URL"] == "http://x:8123"
    assert os.environ["HA_TOKEN"] == "from_env"


def test_find_project_root_walks_up(tmp_path):
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "configuration.yaml").write_text("")
    nested = tmp_path / "a" / "b"
    nested.mkdir(parents=True)
    assert find_project_root(nested) == tmp_path.resolve()
