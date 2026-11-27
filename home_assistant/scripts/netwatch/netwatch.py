#!/usr/bin/env python3
"""netwatch: report which programs on this computer use the network to Home Assistant.

A small watcher of our own, so nothing third-party sits between the computers and the
internet. It runs as the logged-in user, needs only `psutil`, and sends one JSON
report to a Home Assistant webhook. It never blocks or changes anything.

What it notices
  talker     a program holding a connection to a public internet address
  listener   a program accepting connections from other machines
  temp       a program doing either while running from a temp or downloads folder,
             which is where droppers and bundled spyware usually start from
  antivirus  on Windows, whether Microsoft Defender is on, current, and has caught anything

It keeps a list of what it has seen in `state.json`. For the first few days
(`learn_days`) everything is learned silently; after that, anything not on the list
is reported as new for `hold_hours` and then joins the list. A "temp" sighting is
reported even while learning.

What it cannot do: it has no list of known spyware, it only sees this computer, it
samples (a connection shorter than the sample interval can be missed), and anything
running with administrator rights can hide from it or stop it. It is a "something
changed" alarm, not an antivirus.

Usage
  netwatch.py --once --print     one sample, print the report, send nothing
  netwatch.py                    run forever (what the installers set up)

Settings come from config.json beside state.json (see default_dir()):
  {"url": "http://<home-assistant>:8123/api/webhook/<id>", "name": "Office PC"}
"""

from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import os
import platform
import re
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

SAMPLE_SECONDS = 20
REPORT_SECONDS = 300
ANTIVIRUS_SECONDS = 1800
LEARN_DAYS = 3
HOLD_HOURS = 24
MAX_FINDINGS = 20

# A path segment that is only a version number, e.g. "131.0.6778.86" or "app-1.0.9173".
_VERSION_SEGMENT = re.compile(r"^(?:app-|v)?\d+(?:[._-]\d+)+$", re.IGNORECASE)
# The version inside a Windows Store package folder: Name_1.2.3.0_x64__publisher.
_STORE_VERSION = re.compile(r"_\d+(?:\.\d+)+_")

_RISKY_DIRS = (
    "/appdata/local/temp/",
    "/windows/temp/",
    "/users/public/",
    "/downloads/",
    "/tmp/",
    "/var/tmp/",
    "/dev/shm/",
)


def default_dir() -> Path:
    if os.name == "nt":
        return Path(os.environ.get("LOCALAPPDATA", Path.home())) / "netwatch"
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "netwatch"


def normalize_exe(path: str) -> str:
    """Make a program path stable across its own updates.

    Self-updating apps live in versioned folders, so without this every update
    would look like a new program.
    """
    parts = path.replace("\\", "/").split("/")
    out = []
    for part in parts:
        if _VERSION_SEGMENT.match(part):
            out.append("*")
        else:
            out.append(_STORE_VERSION.sub("_*_", part))
    return "/".join(out).lower()


def is_risky_location(path: str) -> bool:
    p = path.replace("\\", "/").lower()
    return any(d in p for d in _RISKY_DIRS)


def is_public(ip: str) -> bool:
    try:
        return ipaddress.ip_address(ip.split("%")[0]).is_global
    except ValueError:
        return False


def is_exposed(ip: str) -> bool:
    """True when a listening address can be reached from another machine."""
    try:
        return not ipaddress.ip_address(ip.split("%")[0]).is_loopback
    except ValueError:
        return True


def finding_id(key: str) -> str:
    return hashlib.sha1(key.encode()).hexdigest()[:8]


def observe(connections, exe_of) -> dict[str, dict]:
    """Turn raw connections into sightings keyed by a stable string.

    `connections` yields (pid, status, local_ip, local_port, remote_ip, remote_port);
    `exe_of(pid)` returns (path_or_None, name).
    """
    seen: dict[str, dict] = {}
    cache: dict[int, tuple[str | None, str]] = {}
    for pid, status, lip, lport, rip, rport in connections:
        if pid is None:
            continue
        if pid not in cache:
            cache[pid] = exe_of(pid)
        path, name = cache[pid]
        ident = normalize_exe(path) if path else f"?/{name.lower()}"
        shown = path or name

        if rip and is_public(rip):
            kind, key, detail = "talker", f"talker|{ident}", f"to {rip}:{rport}"
        elif not rip and status in ("LISTEN", "NONE") and lip is not None and is_exposed(lip):
            # UDP sockets have no state; an unconnected one bound to a fixed low-ish
            # port is a listener, an ephemeral one is just a client waiting for replies.
            if status == "NONE" and lport >= 32768:
                continue
            kind, key, detail = "listener", f"listener|{ident}|{lport}", f"port {lport}"
        else:
            continue

        seen.setdefault(key, {"kind": kind, "name": name, "path": shown, "detail": detail})
        if path and is_risky_location(path):
            seen.setdefault(
                f"temp|{ident}",
                {"kind": "temp", "name": name, "path": shown, "detail": detail},
            )
    return seen


def update_state(state: dict, seen: dict[str, dict], now: float, learn_days: float) -> dict:
    """Record sightings; flag the ones that are new once learning is over."""
    state.setdefault("created", now)
    known = state.setdefault("known", {})
    learning = now < state["created"] + learn_days * 86400
    for key, sight in seen.items():
        if key in known:
            continue
        flagged = sight["kind"] == "temp" or not learning
        known[key] = {**sight, "first_seen": now, "flagged": flagged}
    return state


def current_findings(state: dict, now: float, hold_hours: float) -> list[dict]:
    out = []
    for key, item in state.get("known", {}).items():
        if item.get("flagged") and now - item["first_seen"] < hold_hours * 3600:
            out.append(
                {
                    "id": finding_id(key),
                    "kind": item["kind"],
                    "name": item["name"],
                    "path": item["path"],
                    "detail": item["detail"],
                    "first_seen": int(item["first_seen"]),
                }
            )
    out.sort(key=lambda f: -f["first_seen"])
    return out[:MAX_FINDINGS]


def build_report(state: dict, name: str, antivirus: dict | None, now: float, cfg: dict) -> dict:
    known = state.get("known", {})
    learn_end = state.get("created", now) + cfg["learn_days"] * 86400
    return {
        "host": socket.gethostname(),
        "name": name,
        "os": platform.system(),
        "talkers": sum(1 for v in known.values() if v["kind"] == "talker"),
        "listeners": sum(1 for v in known.values() if v["kind"] == "listener"),
        "learning_until": int(learn_end) if now < learn_end else None,
        "findings": current_findings(state, now, cfg["hold_hours"]),
        "antivirus": antivirus,
    }


# --- the parts that touch the machine -------------------------------------------------


def read_connections():
    """Yield (pid, status, lip, lport, rip, rport) for every socket we may see.

    Windows and Linux list every socket in one call. macOS refuses that without
    root, so fall back to asking each of our own processes.
    """
    import psutil

    def unpack(c, pid):
        lip, lport = (c.laddr.ip, c.laddr.port) if c.laddr else (None, 0)
        rip, rport = (c.raddr.ip, c.raddr.port) if c.raddr else (None, 0)
        return pid, c.status, lip, lport, rip, rport

    try:
        for c in psutil.net_connections(kind="inet"):
            yield unpack(c, c.pid)
        return
    except (psutil.AccessDenied, PermissionError):
        pass
    for proc in psutil.process_iter(["pid"]):
        try:
            for c in proc.net_connections(kind="inet"):
                yield unpack(c, proc.pid)
        except (psutil.Error, PermissionError):
            continue


def exe_of(pid: int) -> tuple[str | None, str]:
    import psutil

    try:
        proc = psutil.Process(pid)
        name = proc.name()
    except psutil.Error:
        return None, f"pid {pid}"
    try:
        return proc.exe() or None, name
    except (psutil.Error, OSError):
        return None, name


_DEFENDER_PS = (
    "$s = Get-MpComputerStatus; "
    "$t = $null; try { $t = @(Get-MpThreatDetection -ErrorAction Stop | "
    "Where-Object { $_.InitialDetectionTime -gt (Get-Date).AddDays(-7) }).Count } catch {}; "
    '[pscustomobject]@{ realtime = $s.RealTimeProtectionEnabled; mode = "$($s.AMRunningMode)"; '
    "definitions_age_days = $s.AntivirusSignatureAge; threats_7d = $t } | ConvertTo-Json -Compress"
)


def read_antivirus() -> dict | None:
    """Microsoft Defender's own status on Windows; None elsewhere or when unreadable."""
    if os.name != "nt":
        return None
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", _DEFENDER_PS],
            capture_output=True,
            text=True,
            timeout=60,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        ).stdout
        data = json.loads(out)
    except (OSError, subprocess.SubprocessError, ValueError):
        return None
    return {k: data.get(k) for k in ("realtime", "mode", "definitions_age_days", "threats_7d")}


def load_json(path: Path, default: dict) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def save_json(path: Path, data: dict) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=1), encoding="utf-8")
    tmp.replace(path)


def send(url: str, report: dict) -> bool:
    req = urllib.request.Request(
        url,
        data=json.dumps(report).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        # Home Assistant is on the home network; never route the report via a proxy.
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(req, timeout=15):
            return True
    except OSError:
        return False


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--dir", type=Path, default=default_dir(), help="config and state folder")
    ap.add_argument("--once", action="store_true", help="take one sample, report, and exit")
    ap.add_argument("--print", action="store_true", help="print the report instead of sending")
    args = ap.parse_args(argv)

    args.dir.mkdir(parents=True, exist_ok=True)
    cfg = {"learn_days": LEARN_DAYS, "hold_hours": HOLD_HOURS, "name": socket.gethostname()}
    cfg.update(load_json(args.dir / "config.json", {}))
    if not args.print and not cfg.get("url"):
        print(f"No webhook url in {args.dir / 'config.json'}", file=sys.stderr)
        return 2

    state_path = args.dir / "state.json"
    state = load_json(state_path, {})
    antivirus, av_at, sent_at, sent_ids = None, 0.0, 0.0, None

    while True:
        now = time.time()
        update_state(state, observe(read_connections(), exe_of), now, cfg["learn_days"])
        save_json(state_path, state)
        if now - av_at >= ANTIVIRUS_SECONDS:
            antivirus, av_at = read_antivirus(), now

        report = build_report(state, cfg["name"], antivirus, now, cfg)
        ids = [f["id"] for f in report["findings"]]
        if args.print:
            print(json.dumps(report, indent=2))
        elif (ids != sent_ids or now - sent_at >= REPORT_SECONDS) and send(cfg["url"], report):
            sent_at, sent_ids = now, ids
        if args.once:
            return 0
        time.sleep(SAMPLE_SECONDS)


if __name__ == "__main__":
    sys.exit(main())
