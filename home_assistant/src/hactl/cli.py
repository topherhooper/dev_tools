"""Command-line entry point: `hactl <command>`."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections.abc import Sequence

import httpx

from hactl import sync
from hactl.client import HAClient, HAError
from hactl.settings import Settings


def _client(settings: Settings) -> HAClient:
    return HAClient(settings.url, settings.token)


def _require_ssh(settings: Settings) -> str:
    if not settings.ssh:
        raise HAError("HA_SSH must be set for deploy/pull (e.g. root@homeassistant.local)")
    return settings.ssh


def cmd_ping(args: argparse.Namespace, settings: Settings) -> int:
    with _client(settings) as ha:
        print(ha.ping())
        cfg = ha.config()
        print(f"{cfg.get('location_name')} — Home Assistant {cfg.get('version')}")
    return 0


def cmd_states(args: argparse.Namespace, settings: Settings) -> int:
    with _client(settings) as ha:
        states = ha.unavailable() if args.unavailable else ha.states(args.domain)
    if args.json:
        print(json.dumps(states, indent=2))
        return 0
    for s in states:
        name = s.get("attributes", {}).get("friendly_name", "")
        print(f"{s['entity_id']:<50} {s['state']:<15} {name}")
    return 0


def cmd_call(args: argparse.Namespace, settings: Settings) -> int:
    domain, _, service = args.service.partition(".")
    if not service:
        raise HAError("service must look like domain.service, e.g. light.turn_on")
    data = json.loads(args.data) if args.data else {}
    with _client(settings) as ha:
        changed = ha.call_service(domain, service, data)
    for s in changed or []:
        print(f"{s['entity_id']} -> {s['state']}")
    return 0


def _check(ha: HAClient) -> bool:
    result = ha.check_config()
    if result.get("result") == "valid":
        print("Config is valid.")
        return True
    print(f"Config is INVALID:\n{result.get('errors')}", file=sys.stderr)
    return False


def cmd_check(args: argparse.Namespace, settings: Settings) -> int:
    with _client(settings) as ha:
        return 0 if _check(ha) else 1


def cmd_reload(args: argparse.Namespace, settings: Settings) -> int:
    with _client(settings) as ha:
        if not _check(ha):
            return 1
        if args.restart:
            ha.restart()
            print("Restart requested.")
        else:
            ha.reload_all()
            print("Reloaded all YAML config.")
    return 0


def cmd_deploy(args: argparse.Namespace, settings: Settings) -> int:
    sync.run(
        sync.push_command(
            _require_ssh(settings),
            settings.remote_config_dir,
            include_secrets=args.include_secrets,
            dry_run=args.dry_run,
        )
    )
    if args.dry_run or args.no_reload:
        return 0
    return cmd_reload(args, settings)


def cmd_pull(args: argparse.Namespace, settings: Settings) -> int:
    sync.run(
        sync.pull_command(_require_ssh(settings), settings.remote_config_dir, dry_run=args.dry_run)
    )
    if not args.dry_run:
        print("Pulled UI-managed files; review with `git diff config/`.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hactl", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("ping", help="check connectivity and show HA version").set_defaults(
        func=cmd_ping
    )

    p = sub.add_parser("states", help="list entity states")
    p.add_argument("--domain", help="only this domain, e.g. light")
    p.add_argument("--unavailable", action="store_true", help="only unavailable/unknown")
    p.add_argument("--json", action="store_true", help="raw JSON output")
    p.set_defaults(func=cmd_states)

    p = sub.add_parser("call", help="call a service, e.g. `hactl call light.turn_on`")
    p.add_argument("service", help="domain.service")
    p.add_argument("--data", help='JSON service data, e.g. \'{"entity_id": "light.kitchen"}\'')
    p.set_defaults(func=cmd_call)

    sub.add_parser("check", help="validate config on the HA host").set_defaults(func=cmd_check)

    p = sub.add_parser("reload", help="check config, then reload YAML (or restart)")
    p.add_argument("--restart", action="store_true", help="full restart instead of reload")
    p.set_defaults(func=cmd_reload)

    p = sub.add_parser("deploy", help="rsync config/ to the HA host, check, then reload")
    p.add_argument("--dry-run", action="store_true", help="show what would be copied")
    p.add_argument("--no-reload", action="store_true", help="copy only; skip check and reload")
    p.add_argument("--restart", action="store_true", help="restart instead of reload")
    p.add_argument(
        "--include-secrets", action="store_true", help="also copy local config/secrets.yaml"
    )
    p.set_defaults(func=cmd_deploy)

    p = sub.add_parser("pull", help="fetch UI-edited automations/scripts/scenes into config/")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_pull)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args, Settings.from_env())
    except (HAError, httpx.HTTPError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except subprocess.CalledProcessError as exc:
        print(f"error: {exc.cmd[0]} exited with {exc.returncode}", file=sys.stderr)
        return exc.returncode


if __name__ == "__main__":
    sys.exit(main())
