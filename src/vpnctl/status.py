"""Parse OpenVPN status log (legacy CSV and status-version >= 2)."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class OnlineClient:
    cn: str
    real_address: str = ""
    virtual_address: str = ""
    bytes_received: int = 0
    bytes_sent: int = 0
    connected_since: str = ""
    client_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_HEADER_ALIASES = {
    "common name": "cn",
    "real address": "real",
    "virtual address": "virtual",
    "bytes received": "bytes_in",
    "bytes sent": "bytes_out",
    "connected since": "since",
    "client id": "client_id",
    "common_name": "cn",
    "real_address": "real",
    "virtual_address": "virtual",
    "bytes_received": "bytes_in",
    "bytes_sent": "bytes_out",
    "connected_since": "since",
}


def _split_record(line: str) -> list[str]:
    if "\t" in line:
        return line.split("\t")
    return [p.strip() for p in line.split(",")]


def _header_map(names: list[str]) -> dict[str, int]:
    out: dict[str, int] = {}
    for idx, name in enumerate(names):
        key = _HEADER_ALIASES.get(name.strip().lower(), name.strip().lower())
        out[key] = idx
    return out


def _field(parts: list[str], cols: dict[str, int], key: str, fallback: int) -> str:
    idx = cols.get(key, fallback)
    if 0 <= idx < len(parts):
        return parts[idx].strip()
    if 0 <= fallback < len(parts):
        return parts[fallback].strip()
    return ""


def _as_int(value: str) -> int:
    try:
        return int(str(value).strip() or "0")
    except ValueError:
        return 0


def _looks_like_ip(value: str) -> bool:
    return bool(re.match(r"^\d{1,3}(\.\d{1,3}){3}", value or ""))


def parse_openvpn_status(text: str) -> list[OnlineClient]:
    clients: list[OnlineClient] = []
    routing_virt: dict[str, str] = {}
    section: str | None = None
    client_cols: dict[str, int] = {}
    route_cols: dict[str, int] = {}
    client_has_virtual = False

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = _split_record(line)
        record_type = parts[0] if parts else ""

        if record_type == "HEADER" and len(parts) >= 3:
            if parts[1] == "CLIENT_LIST":
                section = "client"
                client_cols = _header_map(parts[2:])
                client_has_virtual = "virtual" in client_cols
            elif parts[1] == "ROUTING_TABLE":
                section = "routing"
                route_cols = _header_map(parts[2:])
            continue

        if record_type == "CLIENT_LIST" and len(parts) >= 3:
            row = _parse_client_row(parts[1:], client_cols, client_has_virtual)
            if row:
                clients.append(row)
            continue

        if record_type == "ROUTING_LIST" and len(parts) >= 3:
            route_parts = parts[1:]
            virt = _field(route_parts, route_cols, "virtual", 0)
            cn = _field(route_parts, route_cols, "cn", 1)
            if cn and _looks_like_ip(virt):
                routing_virt[cn] = virt
            continue

        if record_type in ("TITLE", "TIME", "GLOBAL_STATS", "END"):
            continue

        if line.startswith("OpenVPN CLIENT LIST"):
            section = "client"
            client_cols = {}
            client_has_virtual = False
            continue
        if line.startswith("ROUTING TABLE"):
            section = "routing"
            route_cols = {}
            continue
        if line.startswith("GLOBAL STATS") or line.startswith("TITLE"):
            section = None
            continue
        if section == "client" and (
            line.lower().startswith("common name,")
            or line.lower().startswith("common name\t")
        ):
            sep = "\t" if "\t" in line else ","
            client_cols = _header_map([h.strip() for h in line.split(sep)])
            client_has_virtual = "virtual" in client_cols
            continue
        if section == "routing" and (
            line.lower().startswith("virtual address,")
            or line.lower().startswith("virtual address\t")
        ):
            sep = "\t" if "\t" in line else ","
            route_cols = _header_map([h.strip() for h in line.split(sep)])
            continue
        if line.startswith("Updated,") or line.startswith("END"):
            continue

        legacy = parts if "\t" not in raw_line else [p.strip() for p in line.split(",")]
        if section == "routing" and len(legacy) >= 2:
            virt = _field(legacy, route_cols, "virtual", 0)
            cn = _field(legacy, route_cols, "cn", 1)
            if cn and _looks_like_ip(virt):
                routing_virt[cn] = virt
            continue
        if section != "client" or len(legacy) < 3:
            continue
        row = _parse_client_row(legacy, client_cols, client_has_virtual)
        if row:
            clients.append(row)

    for client in clients:
        if not client.virtual_address and client.cn in routing_virt:
            client.virtual_address = routing_virt[client.cn]
    return clients


def _parse_client_row(
    parts: list[str],
    cols: dict[str, int],
    client_has_virtual: bool,
) -> OnlineClient | None:
    cn = _field(parts, cols, "cn", 0)
    if not cn or cn.lower() in ("undef", "common name"):
        return None
    real = _field(parts, cols, "real", 1)
    virtual = _field(parts, cols, "virtual", 2) if client_has_virtual else ""
    # Legacy without virtual: Common Name,Real Address,Bytes Received,Bytes Sent,Connected Since
    if client_has_virtual:
        bytes_in = _as_int(_field(parts, cols, "bytes_in", 3))
        bytes_out = _as_int(_field(parts, cols, "bytes_out", 4))
        since = _field(parts, cols, "since", 5)
        client_id = _field(parts, cols, "client_id", 9)
    else:
        bytes_in = _as_int(_field(parts, cols, "bytes_in", 2))
        bytes_out = _as_int(_field(parts, cols, "bytes_out", 3))
        since = _field(parts, cols, "since", 4)
        client_id = _field(parts, cols, "client_id", -1)
    return OnlineClient(
        cn=cn,
        real_address=real,
        virtual_address=virtual if _looks_like_ip(virtual) else "",
        bytes_received=bytes_in,
        bytes_sent=bytes_out,
        connected_since=since,
        client_id=client_id,
    )


def read_online_clients(status_path: Path) -> list[OnlineClient]:
    if not status_path.is_file():
        return []
    text = status_path.read_text(encoding="utf-8", errors="replace")
    return parse_openvpn_status(text)
