import importlib.util
from pathlib import Path

import pytest

_PATH = Path(__file__).parent.parent / "scripts" / "netwatch" / "netwatch.py"
_spec = importlib.util.spec_from_file_location("netwatch", _PATH)
netwatch = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(netwatch)

DAY = 86400
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
DROPPER = r"C:\Users\me\AppData\Local\Temp\x\setup.exe"


def exe_table(table):
    return lambda pid: table[pid]


@pytest.mark.parametrize(
    ("a", "b"),
    [
        (
            r"C:\Users\me\AppData\Local\Discord\app-1.0.9173\Discord.exe",
            r"C:\Users\me\AppData\Local\Discord\app-1.0.9180\Discord.exe",
        ),
        (
            r"C:\Program Files\WindowsApps\Microsoft.Foo_1.2.3.0_x64__8wekyb3d8bbwe\Foo.exe",
            r"C:\Program Files\WindowsApps\Microsoft.Foo_1.4.0.0_x64__8wekyb3d8bbwe\Foo.exe",
        ),
        ("/opt/app/131.0.6778.86/app", "/opt/app/132.0.1.2/app"),
    ],
)
def test_an_update_does_not_look_like_a_new_program(a, b):
    assert netwatch.normalize_exe(a) == netwatch.normalize_exe(b)


def test_different_programs_stay_different():
    assert netwatch.normalize_exe("/usr/bin/curl") != netwatch.normalize_exe("/usr/bin/wget")


def test_public_and_private_addresses():
    assert netwatch.is_public("8.8.8.8")
    assert not netwatch.is_public("192.168.86.20")
    assert not netwatch.is_public("127.0.0.1")
    assert not netwatch.is_public("fe80::1%eth0")
    assert not netwatch.is_public("not an address")


def test_observe_sorts_connections_into_talkers_and_listeners():
    conns = [
        (1, "ESTABLISHED", "192.168.86.43", 50000, "142.250.1.1", 443),  # talker
        (1, "ESTABLISHED", "192.168.86.43", 50001, "192.168.86.20", 8123),  # LAN: ignored
        (2, "LISTEN", "0.0.0.0", 61208, None, 0),  # listener
        (2, "LISTEN", "127.0.0.1", 9000, None, 0),  # loopback only: ignored
        (3, "NONE", "0.0.0.0", 5353, None, 0),  # UDP service port
        (3, "NONE", "0.0.0.0", 51234, None, 0),  # UDP client port: ignored
        (None, "ESTABLISHED", "192.168.86.43", 50002, "1.1.1.1", 443),  # no owner: ignored
    ]
    seen = netwatch.observe(
        conns,
        exe_table({1: (CHROME, "chrome.exe"), 2: (None, "svc"), 3: ("/usr/bin/mdns", "mdns")}),
    )
    assert sorted(v["kind"] for v in seen.values()) == ["listener", "listener", "talker"]
    assert "listener|?/svc|61208" in seen
    assert "listener|/usr/bin/mdns|5353" in seen


def test_a_program_in_a_temp_folder_is_also_a_temp_sighting():
    conns = [(7, "ESTABLISHED", "192.168.86.43", 50000, "93.184.216.34", 443)]
    seen = netwatch.observe(conns, exe_table({7: (DROPPER, "setup.exe")}))
    assert sorted(v["kind"] for v in seen.values()) == ["talker", "temp"]


def sight(kind="talker", name="chrome.exe"):
    return {"kind": kind, "name": name, "path": name, "detail": "to 1.2.3.4:443"}


def test_learning_is_silent_then_new_programs_are_flagged_for_a_day():
    state = {}
    netwatch.update_state(state, {"talker|chrome": sight()}, now=0, learn_days=3)
    assert netwatch.current_findings(state, now=10, hold_hours=24) == []

    after = 3 * DAY + 1
    netwatch.update_state(
        state, {"talker|chrome": sight(), "talker|odd": sight(name="odd.exe")}, after, 3
    )
    found = netwatch.current_findings(state, after + 60, hold_hours=24)
    assert [f["name"] for f in found] == ["odd.exe"]
    assert found[0]["id"] == netwatch.finding_id("talker|odd")

    # A day later it has joined the known list and seeing it again changes nothing.
    netwatch.update_state(state, {"talker|odd": sight(name="odd.exe")}, after + DAY + 1, 3)
    assert netwatch.current_findings(state, after + DAY + 1, hold_hours=24) == []


def test_temp_sightings_are_flagged_even_while_learning():
    state = {}
    netwatch.update_state(state, {"temp|x": sight(kind="temp", name="setup.exe")}, 0, 3)
    assert [f["kind"] for f in netwatch.current_findings(state, 5, 24)] == ["temp"]


def test_report_counts_and_learning_window():
    state = {}
    seen = {"talker|a": sight(), "listener|b|22": sight(kind="listener", name="sshd")}
    netwatch.update_state(state, seen, now=0, learn_days=3)
    cfg = {"learn_days": 3, "hold_hours": 24}
    report = netwatch.build_report(state, "Office PC", None, now=100, cfg=cfg)
    assert (report["talkers"], report["listeners"]) == (1, 1)
    assert report["learning_until"] == 3 * DAY
    assert report["name"] == "Office PC"
    later = netwatch.build_report(state, "Office PC", None, now=4 * DAY, cfg=cfg)
    assert later["learning_until"] is None


def test_runs_end_to_end_on_this_machine(tmp_path, capsys):
    pytest.importorskip("psutil")
    assert netwatch.main(["--dir", str(tmp_path), "--once", "--print"]) == 0
    assert '"findings"' in capsys.readouterr().out
    assert (tmp_path / "state.json").exists()
