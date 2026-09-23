import os
from pathlib import Path

from hactl.settings import find_project_root, load_dotenv
from hactl.sync import pull_command, push_command

LOCAL = Path("/repo/config")


def test_push_excludes_secrets_by_default_and_never_deletes():
    cmd = push_command("root@ha", "/config/", local_dir=LOCAL)
    assert "--delete" not in cmd
    assert cmd[-2:] == ["/repo/config/", "root@ha:/config/"]
    excluded = [cmd[i + 1] for i, a in enumerate(cmd) if a == "--exclude"]
    assert "secrets.yaml" in excluded
    assert ".storage/" in excluded


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
