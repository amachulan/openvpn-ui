"""vpnctl command-line entrypoint."""

from __future__ import annotations

import argparse
import os
import secrets
import sys
from importlib import resources
from pathlib import Path


def _read_asset_text(name: str, *relative_candidates: str) -> str | None:
    """Read install asset text from package data or known filesystem locations."""
    try:
        packaged = resources.files("vpnctl").joinpath("data", name)
        return packaged.read_text(encoding="utf-8")
    except (FileNotFoundError, ModuleNotFoundError, AttributeError, TypeError, OSError):
        pass

    env_root = os.environ.get("VPNCTL_INSTALL_DIR", "").strip()
    search_roots: list[Path] = []
    if env_root:
        search_roots.append(Path(env_root))
    search_roots.extend(
        [
            Path("/opt/vpnctl"),
            Path(__file__).resolve().parents[2],
            Path(__file__).resolve().parents[3],
        ]
    )
    for root in search_roots:
        for rel in relative_candidates:
            candidate = root / rel
            if candidate.is_file():
                return candidate.read_text(encoding="utf-8")
    return None


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
    example_text = _read_asset_text(
        "vpnctl.yaml.example",
        "config/vpnctl.yaml.example",
        "vpnctl.yaml.example",
    )
    unit_text = _read_asset_text(
        "vpnctl.service",
        "deploy/vpnctl.service",
        "vpnctl.service",
    )

    config_dir = Path(args.config_dir)
    data_dir = Path(args.data_dir)
    config_path = config_dir / "config.yaml"

    config_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "clients").mkdir(parents=True, exist_ok=True)

    if not config_path.exists():
        if not example_text:
            print(
                "example config missing (expected packaged data or /opt/vpnctl/config/)",
                file=sys.stderr,
            )
            return 1
        token = secrets.token_hex(32)
        text = example_text.replace("token: change-me", f"token: {token}")
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
    if args.systemd:
        if not unit_text:
            print("systemd unit template missing; skipped", file=sys.stderr)
        else:
            euid = os.geteuid() if hasattr(os, "geteuid") else 1
            if euid != 0:
                print("skipping systemd unit install (not root)", file=sys.stderr)
            else:
                unit_dst.write_text(unit_text, encoding="utf-8")
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
