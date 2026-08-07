"""Resolve and persist OpenVPN UDP/TCP instance configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import _config_file_path, _load_on_disk, path_from_cfg, write_config_file
from .server_conf import parse_server_conf


INSTANCE_IDS = ("udp", "tcp")


def _proto_family(proto: str | None) -> str:
    p = (proto or "udp").lower()
    if p.startswith("tcp"):
        return "tcp"
    return "udp"


def normalize_listen_proto(family: str, current: str | None) -> str:
    cur = (current or "").lower()
    if family == "tcp":
        if cur in {"tcp", "tcp6"}:
            return cur
        return "tcp"
    if cur in {"udp", "udp6"}:
        return cur
    return "udp"


def detect_primary_family(cfg: dict[str, Any]) -> str:
    conf = path_from_cfg(cfg, "server_conf")
    if conf.is_file():
        text = conf.read_text(encoding="utf-8", errors="replace")
        return _proto_family(parse_server_conf(text).proto)
    return "udp"


def default_instances(cfg: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Build default udp/tcp instance map from paths.server_conf."""
    primary_conf = path_from_cfg(cfg, "server_conf")
    server_dir = path_from_cfg(cfg, "openvpn_server_dir")
    primary_family = detect_primary_family(cfg)
    legacy_unit = str((cfg.get("openvpn") or {}).get("service") or "").strip()
    primary_unit = legacy_unit or "openvpn-server@server"

    if primary_family == "tcp":
        return {
            "tcp": {
                "enabled": primary_conf.is_file(),
                "conf": str(primary_conf),
                "service": primary_unit,
                "port": 443,
                "primary": True,
            },
            "udp": {
                "enabled": False,
                "conf": str(server_dir / "server-udp.conf"),
                "service": "openvpn-server@server-udp",
                "port": 1194,
                "primary": False,
            },
        }
    return {
        "udp": {
            "enabled": primary_conf.is_file(),
            "conf": str(primary_conf),
            "service": primary_unit,
            "port": 1194,
            "primary": True,
        },
        "tcp": {
            "enabled": False,
            "conf": str(server_dir / "server-tcp.conf"),
            "service": "openvpn-server@server-tcp",
            "port": 443,
            "primary": False,
        },
    }


def resolve_instances(cfg: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Merge defaults with cfg.openvpn.instances; infer enabled from conf file."""
    base = default_instances(cfg)
    overlay = dict((cfg.get("openvpn") or {}).get("instances") or {})
    out: dict[str, dict[str, Any]] = {}
    for iid in INSTANCE_IDS:
        row = dict(base[iid])
        user = overlay.get(iid) or {}
        if isinstance(user, dict):
            for key in ("enabled", "conf", "service", "port", "primary"):
                if key in user and user[key] is not None:
                    row[key] = user[key]
        conf_path = Path(str(row["conf"]))
        # If secondary conf exists on disk, treat as enabled unless explicitly false in overlay.
        if iid in overlay and "enabled" in (overlay.get(iid) or {}):
            row["enabled"] = bool((overlay.get(iid) or {}).get("enabled"))
        elif not row.get("primary"):
            row["enabled"] = conf_path.is_file()
        else:
            row["enabled"] = conf_path.is_file()
        row["port"] = int(row.get("port") or (443 if iid == "tcp" else 1194))
        row["id"] = iid
        out[iid] = row
    # Ensure exactly one primary flag.
    primaries = [i for i, r in out.items() if r.get("primary")]
    if not primaries:
        fam = detect_primary_family(cfg)
        out[fam]["primary"] = True
        out["tcp" if fam == "udp" else "udp"]["primary"] = False
    return out


def primary_instance_id(cfg: dict[str, Any]) -> str:
    for iid, row in resolve_instances(cfg).items():
        if row.get("primary"):
            return iid
    return detect_primary_family(cfg)


def get_instance(cfg: dict[str, Any], instance_id: str) -> dict[str, Any]:
    iid = (instance_id or "").strip().lower()
    if iid not in INSTANCE_IDS:
        raise KeyError(f"unknown instance: {instance_id}")
    return resolve_instances(cfg)[iid]


def persist_instances(cfg: dict[str, Any], instances: dict[str, dict[str, Any]]) -> None:
    path = _config_file_path(cfg)
    on_disk = _load_on_disk(path)
    openvpn = dict(on_disk.get("openvpn") or {})
    clean: dict[str, Any] = {}
    for iid in INSTANCE_IDS:
        row = instances.get(iid) or {}
        clean[iid] = {
            "enabled": bool(row.get("enabled")),
            "conf": str(row.get("conf") or ""),
            "service": str(row.get("service") or ""),
            "port": int(row.get("port") or (443 if iid == "tcp" else 1194)),
            "primary": bool(row.get("primary")),
        }
    openvpn["instances"] = clean
    if "service" not in openvpn:
        openvpn["service"] = ""
    on_disk["openvpn"] = openvpn
    write_config_file(path, on_disk)
    cfg_openvpn = dict(cfg.get("openvpn") or {})
    cfg_openvpn["instances"] = clean
    cfg["openvpn"] = cfg_openvpn
    cfg["_config_path"] = str(path)


def enabled_instance_ids(cfg: dict[str, Any]) -> list[str]:
    return [iid for iid, row in resolve_instances(cfg).items() if row.get("enabled")]
