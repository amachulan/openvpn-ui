"""HTTP client IP allowlists for non-loopback binds."""

from __future__ import annotations

import ipaddress
import re
from pathlib import Path
from typing import Any

_SERVER_RE = re.compile(
    r"^\s*server\s+(\d{1,3}(?:\.\d{1,3}){3})\s+(\d{1,3}(?:\.\d{1,3}){3})\b",
    re.IGNORECASE,
)
_SERVER_IPV6_RE = re.compile(
    r"^\s*server-ipv6\s+([0-9a-fA-F:]+/\d+)\b",
    re.IGNORECASE,
)


def is_loopback_bind(host: str) -> bool:
    value = (host or "").strip().lower()
    return value in {"127.0.0.1", "::1", "localhost"}


def parse_vpn_pool_cidrs(server_conf: Path) -> list[str]:
    """Read OpenVPN ``server`` / ``server-ipv6`` directives as CIDRs."""
    if not server_conf.is_file():
        return []
    out: list[str] = []
    for raw in server_conf.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        m = _SERVER_RE.match(line)
        if m:
            network = ipaddress.ip_network(f"{m.group(1)}/{m.group(2)}", strict=False)
            out.append(str(network))
            continue
        m6 = _SERVER_IPV6_RE.match(line)
        if m6:
            try:
                out.append(str(ipaddress.ip_network(m6.group(1), strict=False)))
            except ValueError:
                continue
    return out


def resolve_allow_networks(
    cfg: dict[str, Any],
) -> list[ipaddress.IPv4Network | ipaddress.IPv6Network]:
    api = cfg.get("api") or {}
    networks: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = []
    seen: set[str] = set()

    def _add(cidr: str) -> None:
        text = (cidr or "").strip()
        if not text or text in seen:
            return
        try:
            net = ipaddress.ip_network(text, strict=False)
        except ValueError:
            return
        seen.add(str(net))
        networks.append(net)

    for item in api.get("allow_from") or []:
        _add(str(item))

    if bool(api.get("allow_from_vpn")):
        from .config import path_from_cfg

        try:
            server_conf = path_from_cfg(cfg, "server_conf")
        except KeyError:
            server_conf = Path("/etc/openvpn/server/server.conf")
        for cidr in parse_vpn_pool_cidrs(server_conf):
            _add(cidr)

    return networks


def client_ip_allowed(
    client_ip: str,
    networks: list[ipaddress.IPv4Network | ipaddress.IPv6Network],
) -> bool:
    if not networks:
        return True
    try:
        addr = ipaddress.ip_address((client_ip or "").strip())
    except ValueError:
        return False
    return any(addr in net for net in networks)


def extract_client_ip(headers: dict[str, str], direct_ip: str | None) -> str:
    """Prefer direct peer IP; optionally honor X-Forwarded-For when trusted later."""
    # Direct socket peer is authoritative for allow_from (no spoofable headers yet).
    return (direct_ip or "").strip()
