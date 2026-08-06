"""Load and resolve vpnctl configuration."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG_PATH = Path("/etc/vpnctl/config.yaml")


def default_config() -> dict[str, Any]:
    return {
        "paths": {
            "openvpn_server_dir": "/etc/openvpn/server",
            "easy_rsa_dir": "/etc/openvpn/server/easy-rsa",
            "server_conf": "/etc/openvpn/server/server.conf",
            "client_template": "/etc/openvpn/server/client-template.txt",
            "status_log": "/var/log/openvpn/status.log",
            "crl_publish": "/etc/openvpn/server/crl.pem",
            "client_output_dir": "/var/lib/vpnctl/clients",
            "catalog_db": "/var/lib/vpnctl/catalog.db",
        },
        "openvpn_management": {
            "timeout_seconds": 15,
        },
        "api": {
            "host": "127.0.0.1",
            "port": 8080,
            "token": "change-me",
        },
        "expiry": {
            "warn_days": 30,
        },
        "mail": {
            "enabled": False,
            "smtp_host": "localhost",
            "smtp_port": 25,
            "smtp_user": "",
            "smtp_password": "",
            "use_tls": False,
            "from_addr": "vpnctl@example.com",
            "subject": "Your OpenVPN profile",
        },
        "telegram": {
            "enabled": False,
            "bot_token": "",
            "chat_id": "",
        },
    }


def config_path_env() -> Path:
    raw = os.environ.get("VPNCTL_CONFIG", "").strip()
    if raw:
        return Path(raw)
    return DEFAULT_CONFIG_PATH


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def load_config(path: Path | None = None) -> dict[str, Any]:
    cfg = default_config()
    cfg_path = path or config_path_env()
    if cfg_path.is_file():
        data = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
        if not isinstance(data, dict):
            raise ValueError(f"Config must be a mapping: {cfg_path}")
        cfg = _deep_merge(cfg, data)
    cfg["_config_path"] = str(cfg_path)
    return cfg


def path_from_cfg(cfg: dict[str, Any], key: str) -> Path:
    paths = cfg.get("paths") or {}
    raw = paths.get(key)
    if not raw:
        raise KeyError(f"paths.{key} is not set")
    return Path(str(raw))


def resolve_status_log_path(cfg: dict[str, Any]) -> Path:
    configured = path_from_cfg(cfg, "status_log")
    if configured.is_file():
        return configured
    server_conf = path_from_cfg(cfg, "server_conf")
    if server_conf.is_file():
        for raw in server_conf.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or line.startswith(";"):
                continue
            parts = line.split()
            if len(parts) >= 2 and parts[0].lower() == "status":
                candidate = Path(parts[1])
                if candidate.is_file():
                    return candidate
    return configured


def resolve_management(cfg: dict[str, Any]) -> dict[str, Any]:
    """Return {mode: unix|tcp, path|host|port, timeout}."""
    block = dict(cfg.get("openvpn_management") or {})
    timeout = float(block.get("timeout_seconds") or 15)

    socket_path = str(block.get("socket") or "").strip()
    host = str(block.get("host") or "").strip()
    port = block.get("port")

    if socket_path:
        return {"mode": "unix", "path": socket_path, "timeout": timeout}
    if host and port is not None:
        return {"mode": "tcp", "host": host, "port": int(port), "timeout": timeout}

    server_conf = path_from_cfg(cfg, "server_conf")
    if server_conf.is_file():
        for raw in server_conf.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or line.startswith(";"):
                continue
            parts = line.split()
            if len(parts) < 2 or parts[0].lower() != "management":
                continue
            target = parts[1]
            if len(parts) >= 3 and parts[2].lower() == "unix":
                return {"mode": "unix", "path": target, "timeout": timeout}
            if target.startswith("/"):
                return {"mode": "unix", "path": target, "timeout": timeout}
            try:
                return {
                    "mode": "tcp",
                    "host": target,
                    "port": int(parts[2]),
                    "timeout": timeout,
                }
            except (IndexError, ValueError):
                continue

    # angristan default
    default_sock = Path("/var/run/openvpn-server/server.sock")
    if default_sock.exists():
        return {"mode": "unix", "path": str(default_sock), "timeout": timeout}
    return {"mode": "tcp", "host": "127.0.0.1", "port": 7505, "timeout": timeout}
