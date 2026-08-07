"""Load and resolve openvpn-ui configuration."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG_PATH = Path("/etc/openvpn-ui/config.yaml")


def default_config() -> dict[str, Any]:
    return {
        "paths": {
            "openvpn_server_dir": "/etc/openvpn/server",
            "easy_rsa_dir": "/etc/openvpn/server/easy-rsa",
            "server_conf": "/etc/openvpn/server/server.conf",
            "client_template": "/etc/openvpn/server/client-template.txt",
            "status_log": "/var/log/openvpn/status.log",
            "crl_publish": "/etc/openvpn/server/crl.pem",
            "client_output_dir": "/var/lib/openvpn-ui/clients",
            "catalog_db": "/var/lib/openvpn-ui/catalog.db",
            "server_conf_backup_dir": "/var/lib/openvpn-ui/backups",
        },
        "openvpn": {
            # Override if not angristan default openvpn-server@server.
            "service": "",
        },
        "openvpn_management": {
            "timeout_seconds": 15,
        },
        "api": {
            # 0.0.0.0 = all interfaces (UI reachable over VPN/LAN/public IP).
            # Restrict with allow_from / allow_from_vpn when exposing beyond localhost.
            "host": "0.0.0.0",
            "port": 8080,
            "token": "change-me",
            # Extra CIDRs allowed to reach the UI/API (empty = no IP filter).
            "allow_from": [],
            # If true, also allow the OpenVPN client pool from server.conf (`server ...`).
            "allow_from_vpn": False,
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
            "from_addr": "openvpn-ui@example.com",
            "subject": "Your OpenVPN profile",
        },
        "telegram": {
            "enabled": False,
            "bot_token": "",
            "chat_id": "",
        },
    }


def config_path_env() -> Path:
    raw = os.environ.get("OPENVPN_UI_CONFIG", "").strip()
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


def _config_file_path(cfg: dict[str, Any]) -> Path:
    raw = str(cfg.get("_config_path") or "").strip()
    return Path(raw) if raw else config_path_env()


def _load_on_disk(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Config must be a mapping: {path}")
    return data


def write_config_file(path: Path, data: dict[str, Any]) -> None:
    """Atomically write YAML config (does not include private `_` keys)."""
    clean = {k: v for k, v in data.items() if not str(k).startswith("_")}
    path.parent.mkdir(parents=True, exist_ok=True)
    text = yaml.safe_dump(
        clean,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def public_notify_settings(cfg: dict[str, Any]) -> dict[str, Any]:
    """Mail/Telegram settings for the UI (secrets redacted)."""
    mail = dict(cfg.get("mail") or {})
    tg = dict(cfg.get("telegram") or {})
    password = str(mail.get("smtp_password") or "")
    token = str(tg.get("bot_token") or "")
    return {
        "mail": {
            "enabled": bool(mail.get("enabled")),
            "smtp_host": str(mail.get("smtp_host") or "localhost"),
            "smtp_port": int(mail.get("smtp_port") or 25),
            "smtp_user": str(mail.get("smtp_user") or ""),
            "smtp_password_set": bool(password),
            "use_tls": bool(mail.get("use_tls")),
            "from_addr": str(mail.get("from_addr") or ""),
            "subject": str(mail.get("subject") or ""),
        },
        "telegram": {
            "enabled": bool(tg.get("enabled")),
            "bot_token_set": bool(token),
            "chat_id": str(tg.get("chat_id") or ""),
        },
    }


def normalize_mail_settings(
    incoming: dict[str, Any],
    existing: dict[str, Any] | None = None,
) -> dict[str, Any]:
    prev = dict(existing or {})
    password = str(incoming.get("smtp_password") or "").strip()
    if not password:
        password = str(prev.get("smtp_password") or "")
    return {
        "enabled": bool(incoming.get("enabled")),
        "smtp_host": str(incoming.get("smtp_host") or "localhost").strip() or "localhost",
        "smtp_port": int(incoming.get("smtp_port") or 25),
        "smtp_user": str(incoming.get("smtp_user") or "").strip(),
        "smtp_password": password,
        "use_tls": bool(incoming.get("use_tls")),
        "from_addr": str(incoming.get("from_addr") or "").strip(),
        "subject": str(incoming.get("subject") or "").strip()
        or "Your OpenVPN profile",
    }


def normalize_telegram_settings(
    incoming: dict[str, Any],
    existing: dict[str, Any] | None = None,
) -> dict[str, Any]:
    prev = dict(existing or {})
    token = str(incoming.get("bot_token") or "").strip()
    if not token:
        token = str(prev.get("bot_token") or "")
    return {
        "enabled": bool(incoming.get("enabled")),
        "bot_token": token,
        "chat_id": str(incoming.get("chat_id") or "").strip(),
    }


def persist_notify_settings(
    cfg: dict[str, Any],
    *,
    mail: dict[str, Any],
    telegram: dict[str, Any],
) -> dict[str, Any]:
    """Update in-memory cfg and persist mail/telegram to the config file."""
    path = _config_file_path(cfg)
    on_disk = _load_on_disk(path)
    on_disk["mail"] = mail
    on_disk["telegram"] = telegram
    write_config_file(path, on_disk)
    cfg["mail"] = mail
    cfg["telegram"] = telegram
    cfg["_config_path"] = str(path)
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
