"""vpnctl command-line entrypoint."""

from __future__ import annotations

import argparse
import os
import secrets
import shutil
import sys
from pathlib import Path


def _cmd_serve(args: argparse.Namespace) -> int:
    import uvicorn

    from vpnctl.access import is_loopback_bind, resolve_allow_networks
    from vpnctl.config import load_config

    if args.config:
        os.environ["VPNCTL_CONFIG"] = str(Path(args.config))
    cfg = load_config(Path(args.config) if args.config else None)
    api = cfg.get("api") or {}
    host = args.host or str(api.get("host") or "127.0.0.1")
    port = int(args.port or api.get("port") or 8080)
    allow = resolve_allow_networks(cfg)
    if not is_loopback_bind(host) and not allow:
        print(
            "WARNING: api.host is not loopback and allow_from/allow_from_vpn "
            "are empty — UI/API is reachable from any client IP (token still required).",
            file=sys.stderr,
        )
    elif not is_loopback_bind(host):
        print(
            f"Listening on {host}:{port}; allow_from={', '.join(str(n) for n in allow)}",
            file=sys.stderr,
        )
    uvicorn.run(
        "vpnctl.api.app:create_app",
        host=host,
        port=port,
        reload=False,
        factory=True,
    )
    return 0


def _cmd_install(args: argparse.Namespace) -> int:
    """Copy example config + systemd unit hints (root recommended)."""
    repo_root = Path(__file__).resolve().parents[2]
    example = repo_root / "config" / "vpnctl.yaml.example"
    unit_src = repo_root / "deploy" / "vpnctl.service"

    config_dir = Path(args.config_dir)
    data_dir = Path(args.data_dir)
    config_path = config_dir / "config.yaml"

    config_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "clients").mkdir(parents=True, exist_ok=True)

    if not config_path.exists():
        if not example.is_file():
            print(f"example config missing: {example}", file=sys.stderr)
            return 1
        text = example.read_text(encoding="utf-8")
        token = secrets.token_hex(32)
        text = text.replace("token: change-me", f"token: {token}")
        text = text.replace(
            "catalog_db: /var/lib/vpnctl/catalog.db",
            f"catalog_db: {data_dir / 'catalog.db'}",
        )
        text = text.replace(
            "client_output_dir: /var/lib/vpnctl/clients",
            f"client_output_dir: {data_dir / 'clients'}",
        )
        config_path.write_text(text, encoding="utf-8")
        try:
            config_path.chmod(0o600)
        except OSError:
            pass
        print(f"wrote {config_path}")
        print(f"API token: {token}")
    else:
        print(f"config already exists: {config_path}")

    unit_dst = Path("/etc/systemd/system/vpnctl.service")
    if args.systemd and unit_src.is_file():
        euid = os.geteuid() if hasattr(os, "geteuid") else 1
        if euid != 0:
            print("skipping systemd unit install (not root)", file=sys.stderr)
        else:
            shutil.copy2(unit_src, unit_dst)
            print(f"installed {unit_dst}")
            print("Run: systemctl daemon-reload && systemctl enable --now vpnctl")

    print("Next: ensure OpenVPN was installed with angristan/openvpn-install")
    print(f"Then: VPNCTL_CONFIG={config_path} vpnctl serve")
    return 0


def _cmd_health(_: argparse.Namespace) -> int:
    from vpnctl.service import VpnctlService

    import json

    print(json.dumps(VpnctlService().health(), indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vpnctl", description="OpenVPN management UI/API")
    sub = parser.add_subparsers(dest="command", required=True)

    serve = sub.add_parser("serve", help="Run API + web UI")
    serve.add_argument("--config", help="Path to config.yaml")
    serve.add_argument("--host", help="Bind host")
    serve.add_argument("--port", type=int, help="Bind port")
    serve.set_defaults(func=_cmd_serve)

    install = sub.add_parser("install", help="Write config under /etc/vpnctl")
    install.add_argument("--config-dir", default="/etc/vpnctl")
    install.add_argument("--data-dir", default="/var/lib/vpnctl")
    install.add_argument(
        "--systemd",
        action="store_true",
        help="Install systemd unit (requires root)",
    )
    install.set_defaults(func=_cmd_install)

    health = sub.add_parser("health", help="Print health JSON")
    health.set_defaults(func=_cmd_health)
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    code = args.func(args)
    raise SystemExit(code)


if __name__ == "__main__":
    main()
