"""Parse and patch OpenVPN server.conf (angristan-compatible)."""

from __future__ import annotations

import ipaddress
import re
import shutil
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ALLOWED_PROTOS = frozenset({"udp", "tcp", "udp6", "tcp6"})
ALLOWED_CIPHERS = frozenset(
    {
        "AES-128-GCM",
        "AES-192-GCM",
        "AES-256-GCM",
        "AES-128-CBC",
        "AES-192-CBC",
        "AES-256-CBC",
        "CHACHA20-POLY1305",
    }
)
ALLOWED_AUTH = frozenset({"SHA256", "SHA384", "SHA512", "SHA1"})
ALLOWED_TLS_MIN = frozenset({"1.2", "1.3"})

PROTECTED_PREFIXES = (
    "ca ",
    "cert ",
    "key ",
    "dh ",
    "tls-crypt",
    "tls-auth",
    "tls-crypt-v2",
    "management ",
    "status ",
    "log ",
    "log-append ",
)

PUSH_RE = re.compile(r'^push\s+"(.+)"\s*$', re.IGNORECASE)
REMOTE_RE = re.compile(r"^remote\s+(\S+)(?:\s+(\d+))?\s*$", re.IGNORECASE)
BACKUP_KEEP = 20


class ServerConfError(Exception):
    """Invalid server.conf operation."""


@dataclass
class ServerSettings:
    port: int | None = None
    proto: str | None = None
    duplicate_cn: bool = False
    client_to_client: bool = False
    redirect_gateway: bool = False
    dns: list[str] = field(default_factory=list)
    local_networks: list[str] = field(default_factory=list)
    cipher: str | None = None
    data_ciphers: str | None = None
    auth: str | None = None
    tls_version_min: str | None = None
    tls_mode: str = "none"
    server: str | None = None
    server_ipv6: str | None = None
    dev: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _is_comment_or_blank(line: str) -> bool:
    s = line.strip()
    return not s or s.startswith("#") or s.startswith(";")


def _directive(line: str) -> tuple[str, str]:
    s = line.strip()
    if not s:
        return "", ""
    parts = s.split(None, 1)
    key = parts[0].lower()
    rest = parts[1] if len(parts) > 1 else ""
    return key, rest


def _parse_push_inner(line: str) -> str | None:
    s = line.strip()
    m = PUSH_RE.match(s)
    if not m:
        return None
    return m.group(1).strip()


def _ipv4_netmask(prefix: int) -> str:
    net = ipaddress.IPv4Network(f"0.0.0.0/{prefix}")
    return str(net.netmask)


def cidr_to_push_route(cidr: str) -> str:
    """Return full conf line for a local-network CIDR push."""
    text = (cidr or "").strip()
    try:
        net = ipaddress.ip_network(text, strict=False)
    except ValueError as exc:
        raise ServerConfError(f"invalid CIDR: {cidr}") from exc
    if isinstance(net, ipaddress.IPv4Network):
        return f'push "route {net.network_address} {_ipv4_netmask(net.prefixlen)}"'
    return f'push "route-ipv6 {net.with_prefixlen}"'


def push_route_to_cidr(inner: str) -> str | None:
    """Parse push route / route-ipv6 inner text into CIDR, if possible."""
    parts = inner.split()
    if not parts:
        return None
    if parts[0].lower() == "route" and len(parts) >= 3:
        try:
            addr = ipaddress.IPv4Address(parts[1])
            mask = ipaddress.IPv4Address(parts[2])
            prefix = ipaddress.IPv4Network(f"0.0.0.0/{mask}").prefixlen
            net = ipaddress.IPv4Network(f"{addr}/{prefix}", strict=False)
            return str(net)
        except ValueError:
            return None
    if parts[0].lower() == "route-ipv6" and len(parts) >= 2:
        try:
            return str(ipaddress.IPv6Network(parts[1], strict=False))
        except ValueError:
            return None
    return None


def parse_server_conf(text: str) -> ServerSettings:
    settings = ServerSettings()
    dns: list[str] = []
    networks: list[str] = []
    for raw in text.splitlines():
        if _is_comment_or_blank(raw):
            continue
        key, rest = _directive(raw)
        if key == "port":
            try:
                settings.port = int(rest.split()[0])
            except (ValueError, IndexError):
                pass
        elif key == "proto":
            settings.proto = rest.split()[0].lower() if rest else None
        elif key == "dev":
            settings.dev = rest.split()[0] if rest else None
        elif key == "server":
            settings.server = rest.strip() or None
        elif key == "server-ipv6":
            settings.server_ipv6 = rest.strip() or None
        elif key == "duplicate-cn":
            settings.duplicate_cn = True
        elif key == "client-to-client":
            settings.client_to_client = True
        elif key == "cipher":
            settings.cipher = rest.split()[0] if rest else None
        elif key == "data-ciphers":
            settings.data_ciphers = rest.strip() or None
        elif key == "auth":
            settings.auth = rest.split()[0].upper() if rest else None
        elif key == "tls-version-min":
            settings.tls_version_min = rest.split()[0] if rest else None
        elif key == "tls-crypt-v2" or key.startswith("tls-crypt-v2"):
            settings.tls_mode = "tls-crypt-v2"
        elif key == "tls-crypt":
            if settings.tls_mode == "none":
                settings.tls_mode = "tls-crypt"
        elif key == "tls-auth":
            if settings.tls_mode == "none":
                settings.tls_mode = "tls-auth"
        else:
            inner = _parse_push_inner(raw)
            if not inner:
                continue
            low = inner.lower()
            if low.startswith("dhcp-option dns "):
                dns.append(inner.split(None, 2)[2].strip())
            elif "redirect-gateway" in low:
                settings.redirect_gateway = True
            elif low.startswith("route ") or low.startswith("route-ipv6 "):
                if low.startswith("route-ipv6 2000::/3"):
                    continue
                cidr = push_route_to_cidr(inner)
                if cidr:
                    networks.append(cidr)
    settings.dns = dns
    settings.local_networks = networks
    return settings


def read_server_conf(path: Path) -> tuple[str, ServerSettings]:
    if not path.is_file():
        raise ServerConfError(f"server.conf not found: {path}")
    text = path.read_text(encoding="utf-8", errors="replace")
    return text, parse_server_conf(text)


def validate_settings_patch(patch: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    if "port" in patch and patch["port"] is not None:
        port = int(patch["port"])
        if port < 1 or port > 65535:
            raise ServerConfError("port must be 1–65535")
        out["port"] = port
    if "proto" in patch and patch["proto"] is not None:
        proto = str(patch["proto"]).strip().lower()
        if proto not in ALLOWED_PROTOS:
            raise ServerConfError(f"invalid proto: {proto}")
        out["proto"] = proto
    for flag in ("duplicate_cn", "client_to_client", "redirect_gateway"):
        if flag in patch and patch[flag] is not None:
            out[flag] = bool(patch[flag])
    if "dns" in patch and patch["dns"] is not None:
        dns_list = [str(x).strip() for x in patch["dns"] if str(x).strip()]
        for addr in dns_list:
            try:
                ipaddress.ip_address(addr)
            except ValueError as exc:
                raise ServerConfError(f"invalid DNS address: {addr}") from exc
        out["dns"] = dns_list
    if "local_networks" in patch and patch["local_networks"] is not None:
        nets: list[str] = []
        for raw in patch["local_networks"]:
            text = str(raw).strip()
            if not text:
                continue
            try:
                nets.append(str(ipaddress.ip_network(text, strict=False)))
            except ValueError as exc:
                raise ServerConfError(f"invalid local network: {text}") from exc
        out["local_networks"] = nets
    if "cipher" in patch and patch["cipher"] is not None:
        cipher = str(patch["cipher"]).strip()
        if cipher and cipher not in ALLOWED_CIPHERS:
            raise ServerConfError(f"invalid cipher: {cipher}")
        out["cipher"] = cipher or None
    if "data_ciphers" in patch and patch["data_ciphers"] is not None:
        out["data_ciphers"] = str(patch["data_ciphers"]).strip() or None
    if "auth" in patch and patch["auth"] is not None:
        auth = str(patch["auth"]).strip().upper()
        if auth and auth not in ALLOWED_AUTH:
            raise ServerConfError(f"invalid auth: {auth}")
        out["auth"] = auth or None
    if "tls_version_min" in patch and patch["tls_version_min"] is not None:
        tls = str(patch["tls_version_min"]).strip()
        if tls and tls not in ALLOWED_TLS_MIN:
            raise ServerConfError(f"invalid tls-version-min: {tls}")
        out["tls_version_min"] = tls or None
    return out


def _set_simple_directive(lines: list[str], key: str, value: str | None) -> list[str]:
    key_l = key.lower()
    out: list[str] = []
    seen = False
    for line in lines:
        if _is_comment_or_blank(line):
            out.append(line)
            continue
        dkey, _ = _directive(line)
        if dkey == key_l:
            if value is None:
                continue
            if not seen:
                out.append(f"{key} {value}")
                seen = True
            continue
        out.append(line)
    if value is not None and not seen:
        out.append(f"{key} {value}")
    return out


def _set_flag(lines: list[str], flag: str, enabled: bool) -> list[str]:
    flag_l = flag.lower()
    out: list[str] = []
    seen = False
    for line in lines:
        if _is_comment_or_blank(line):
            out.append(line)
            continue
        dkey, rest = _directive(line)
        if dkey == flag_l and not rest:
            if enabled and not seen:
                out.append(flag)
                seen = True
            continue
        out.append(line)
    if enabled and not seen:
        out.append(flag)
    return out


def _remove_push_matching(lines: list[str], predicate) -> list[str]:
    out: list[str] = []
    for line in lines:
        inner = _parse_push_inner(line)
        if inner is not None and predicate(inner):
            continue
        out.append(line)
    return out


def _insert_pushes_after_dns_anchor(lines: list[str], pushes: list[str]) -> list[str]:
    if not pushes:
        return lines
    insert_at = len(lines)
    last_push = -1
    for i, line in enumerate(lines):
        if _parse_push_inner(line) is not None:
            last_push = i
    if last_push >= 0:
        insert_at = last_push + 1
    else:
        for i, line in enumerate(lines):
            if _is_comment_or_blank(line):
                continue
            s = line.strip().lower()
            if any(s.startswith(p.strip().lower()) for p in PROTECTED_PREFIXES):
                insert_at = i
                break
    return lines[:insert_at] + pushes + lines[insert_at:]


def apply_settings_patch(text: str, patch: dict[str, Any]) -> str:
    """Return updated conf text. `patch` should already be validated."""
    lines = text.splitlines()
    if "port" in patch:
        lines = _set_simple_directive(lines, "port", str(patch["port"]))
    if "proto" in patch:
        lines = _set_simple_directive(lines, "proto", str(patch["proto"]))
    if "duplicate_cn" in patch:
        lines = _set_flag(lines, "duplicate-cn", bool(patch["duplicate_cn"]))
    if "client_to_client" in patch:
        lines = _set_flag(lines, "client-to-client", bool(patch["client_to_client"]))
    if "cipher" in patch:
        lines = _set_simple_directive(
            lines, "cipher", patch["cipher"] if patch["cipher"] else None
        )
    if "data_ciphers" in patch:
        lines = _set_simple_directive(
            lines,
            "data-ciphers",
            patch["data_ciphers"] if patch["data_ciphers"] else None,
        )
    if "auth" in patch:
        lines = _set_simple_directive(
            lines, "auth", patch["auth"] if patch["auth"] else None
        )
    if "tls_version_min" in patch:
        lines = _set_simple_directive(
            lines,
            "tls-version-min",
            patch["tls_version_min"] if patch["tls_version_min"] else None,
        )

    if "dns" in patch:
        lines = _remove_push_matching(
            lines, lambda inner: inner.lower().startswith("dhcp-option dns ")
        )
        dns_pushes = [f'push "dhcp-option DNS {addr}"' for addr in patch["dns"]]
        lines = _insert_pushes_after_dns_anchor(lines, dns_pushes)

    if "local_networks" in patch:

        def is_local_route(inner: str) -> bool:
            low = inner.lower()
            if low.startswith("route-ipv6 2000::/3"):
                return False
            if low.startswith("route ") or low.startswith("route-ipv6 "):
                return push_route_to_cidr(inner) is not None
            return False

        lines = _remove_push_matching(lines, is_local_route)
        route_pushes = [cidr_to_push_route(c) for c in patch["local_networks"]]
        lines = _insert_pushes_after_dns_anchor(lines, route_pushes)

    if "redirect_gateway" in patch:
        lines = _remove_push_matching(
            lines,
            lambda inner: "redirect-gateway" in inner.lower()
            or inner.lower().startswith("route-ipv6 2000::/3")
            or inner.lower() == "block-ipv6",
        )
        if patch["redirect_gateway"]:
            pushes = ['push "redirect-gateway def1 bypass-dhcp"']
            joined = "\n".join(lines).lower()
            if "server-ipv6" in joined:
                pushes.append('push "route-ipv6 2000::/3"')
                pushes.append('push "redirect-gateway ipv6"')
            else:
                pushes.append('push "block-ipv6"')
            lines = _insert_pushes_after_dns_anchor(lines, pushes)

    return "\n".join(lines) + ("\n" if text.endswith("\n") or text == "" else "")


def sync_client_template(
    template_path: Path,
    *,
    port: int | None = None,
    proto: str | None = None,
) -> bool:
    """Update proto / remote port in client-template.txt. Returns True if changed."""
    if not template_path.is_file():
        return False
    text = template_path.read_text(encoding="utf-8", errors="replace")
    new_text = apply_client_endpoint_overrides(text, proto=proto, port=port)
    if new_text == text:
        return False
    template_path.write_text(new_text, encoding="utf-8")
    return True


def apply_client_endpoint_overrides(
    text: str,
    *,
    proto: str | None = None,
    port: int | None = None,
) -> str:
    """Return client template / profile header with proto/remote overridden."""
    lines = text.splitlines()
    out: list[str] = []
    for line in lines:
        stripped = line.strip()
        if proto and stripped.lower().startswith("proto "):
            out.append(f"proto {proto}")
            continue
        m = REMOTE_RE.match(stripped)
        if m and port is not None:
            host = m.group(1)
            out.append(f"remote {host} {port}")
            continue
        out.append(line)
    ending = "\n" if text.endswith("\n") else ""
    return "\n".join(out) + ending


def clone_instance_conf(
    src_text: str,
    *,
    instance_id: str,
    proto: str,
    port: int,
) -> str:
    """Clone a server.conf for a second instance (same PKI/subnet, distinct runtime paths)."""
    iid = instance_id.strip().lower()
    if iid not in {"udp", "tcp"}:
        raise ServerConfError(f"invalid instance id: {instance_id}")
    lines = src_text.splitlines()
    out: list[str] = []
    for line in lines:
        if _is_comment_or_blank(line):
            out.append(line)
            continue
        key, rest = _directive(line)
        if key == "port":
            out.append(f"port {int(port)}")
            continue
        if key == "proto":
            out.append(f"proto {proto}")
            continue
        if key == "status":
            # Keep verb args after path if any.
            parts = rest.split()
            suffix = " " + " ".join(parts[1:]) if len(parts) > 1 else ""
            out.append(f"status /var/log/openvpn/status-{iid}.log{suffix}")
            continue
        if key == "management":
            parts = rest.split()
            if parts and (parts[0].startswith("/") or parts[0].endswith(".sock")):
                out.append(
                    f"management /var/run/openvpn-server/server-{iid}.sock unix"
                )
            elif len(parts) >= 2:
                # TCP management: bump port slightly by family default offset.
                try:
                    host = parts[0]
                    mport = int(parts[1]) + (1 if iid == "tcp" else 2)
                    out.append(f"management {host} {mport}")
                except ValueError:
                    out.append(line)
            else:
                out.append(line)
            continue
        if key == "ifconfig-pool-persist":
            parts = rest.split()
            name = parts[0] if parts else "ipp.txt"
            stem = Path(name).name
            if "." in stem:
                base, ext = stem.rsplit(".", 1)
                new_name = f"{base}-{iid}.{ext}"
            else:
                new_name = f"{stem}-{iid}"
            rest_tail = " " + " ".join(parts[1:]) if len(parts) > 1 else ""
            out.append(f"ifconfig-pool-persist {new_name}{rest_tail}")
            continue
        out.append(line)
    text = "\n".join(out)
    return text + ("\n" if src_text.endswith("\n") or src_text == "" else "")


def backup_file(
    src: Path,
    backup_dir: Path,
    *,
    keep: int = BACKUP_KEEP,
    prefix: str | None = None,
) -> Path:
    if not src.is_file():
        raise ServerConfError(f"cannot backup missing file: {src}")
    backup_dir.mkdir(parents=True, exist_ok=True)
    base = prefix or src.name
    dest = backup_dir / f"{base}.{_utc_stamp()}"
    if dest.exists():
        dest = backup_dir / f"{base}.{_utc_stamp()}.{src.stat().st_mtime_ns}"
    shutil.copy2(src, dest)
    backups = sorted(
        backup_dir.glob(f"{base}.*"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for old in backups[keep:]:
        try:
            old.unlink()
        except OSError:
            pass
    return dest


def list_backups(
    backup_dir: Path, *, prefix: str | None = None
) -> list[dict[str, Any]]:
    if not backup_dir.is_dir():
        return []
    pattern = f"{prefix}.*" if prefix else "server*.conf.*"
    # Also match historical server.conf.* backups when prefix is server.conf
    rows: list[dict[str, Any]] = []
    paths = list(backup_dir.glob(pattern))
    if prefix == "server.conf":
        paths.extend(backup_dir.glob("server.conf.*"))
    seen: set[Path] = set()
    for path in sorted(paths, key=lambda p: p.name, reverse=True):
        if path in seen or not path.is_file():
            continue
        seen.add(path)
        st = path.stat()
        rows.append(
            {
                "id": path.name,
                "path": str(path),
                "size": st.st_size,
                "mtime": datetime.fromtimestamp(st.st_mtime, timezone.utc)
                .replace(microsecond=0)
                .isoformat(),
            }
        )
    return rows


def restore_backup(backup_dir: Path, backup_id: str, dest: Path) -> Path:
    name = Path(backup_id).name
    if name != backup_id or ".." in backup_id or "/" in backup_id or "\\" in backup_id:
        raise ServerConfError("invalid backup id")
    src = backup_dir / name
    if not src.is_file():
        raise ServerConfError(f"backup not found: {backup_id}")
    if dest.is_file():
        backup_file(dest, backup_dir, prefix=dest.name)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    return dest


def write_server_conf(path: Path, text: str, backup_dir: Path) -> Path:
    """Backup existing conf and write new text. Returns backup path (or empty Path)."""
    backup: Path | None = None
    if path.is_file():
        backup = backup_file(path, backup_dir, prefix=path.name)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")
    tmp.replace(path)
    return backup or Path("")
