"""Easy-RSA / angristan PKI adapter."""

from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CN_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
INDEX_CN_RE = re.compile(r"/CN=([^/\s]+)")


class PkiError(Exception):
    """PKI operation failed."""


@dataclass
class CertInfo:
    cn: str
    status: str  # valid | revoked
    serial: str = ""
    expires_at: str = ""
    days_remaining: int | None = None
    cert_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_cn(cn: str) -> str:
    value = (cn or "").strip()
    if not CN_RE.fullmatch(value):
        raise PkiError(
            "client name must be 1-64 chars: letters, digits, underscore, dash"
        )
    return value


def pki_dir(easy_rsa_dir: Path) -> Path:
    return easy_rsa_dir / "pki"


def index_path(easy_rsa_dir: Path) -> Path:
    return pki_dir(easy_rsa_dir) / "index.txt"


def issued_cert_path(easy_rsa_dir: Path, cn: str) -> Path:
    return pki_dir(easy_rsa_dir) / "issued" / f"{cn}.crt"


def private_key_path(easy_rsa_dir: Path, cn: str) -> Path:
    return pki_dir(easy_rsa_dir) / "private" / f"{cn}.key"


def ca_cert_path(easy_rsa_dir: Path) -> Path:
    return pki_dir(easy_rsa_dir) / "ca.crt"


def parse_index_txt(text: str) -> list[CertInfo]:
    """Parse Easy-RSA index.txt into cert rows (latest status per CN wins)."""
    by_cn: dict[str, CertInfo] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line[0] not in "VRE":
            continue
        status_flag = line[0]
        # Tab-separated preferred: status, expiry, revocation, serial, filename, DN
        if "\t" in line:
            parts = line.split("\t")
        else:
            parts = re.split(r"\s+", line, maxsplit=5)
        if len(parts) < 4:
            continue
        # serial is usually field index 3
        serial = parts[3].strip() if len(parts) > 3 else ""
        dn = parts[-1]
        match = INDEX_CN_RE.search(dn)
        if match:
            cn = match.group(1)
        elif "/CN=" in dn:
            cn = dn.split("/CN=", 1)[1].split("/", 1)[0]
        else:
            continue
        if status_flag == "V":
            status = "valid"
        elif status_flag == "E":
            status = "expired"
        else:
            status = "revoked"
        by_cn[cn] = CertInfo(cn=cn, status=status, serial=serial)
    return sorted(by_cn.values(), key=lambda c: c.cn.lower())


def _openssl_enddate(cert_file: Path) -> tuple[str, int | None]:
    if not cert_file.is_file():
        return "", None
    try:
        proc = subprocess.run(
            ["openssl", "x509", "-enddate", "-noout", "-in", str(cert_file)],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "", None
    if proc.returncode != 0:
        return "", None
    # notAfter=Oct  5 12:00:00 2027 GMT
    line = (proc.stdout or "").strip()
    if "=" not in line:
        return "", None
    raw = line.split("=", 1)[1].strip()
    try:
        dt = datetime.strptime(raw, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
    except ValueError:
        try:
            dt = datetime.strptime(raw, "%b %d %H:%M:%S %Y GMT").replace(
                tzinfo=timezone.utc
            )
        except ValueError:
            return raw, None
    now = datetime.now(timezone.utc)
    days = int((dt - now).total_seconds() // 86400)
    return dt.date().isoformat(), days


def list_certificates(easy_rsa_dir: Path) -> list[CertInfo]:
    idx = index_path(easy_rsa_dir)
    if not idx.is_file():
        return []
    certs = parse_index_txt(idx.read_text(encoding="utf-8", errors="replace"))
    for cert in certs:
        cert_file = issued_cert_path(easy_rsa_dir, cert.cn)
        cert.cert_path = str(cert_file) if cert_file.is_file() else ""
        if cert_file.is_file():
            expires, days = _openssl_enddate(cert_file)
            cert.expires_at = expires
            cert.days_remaining = days
            if days is not None and days < 0 and cert.status == "valid":
                cert.status = "expired"
    return certs


def _run_easyrsa(easy_rsa_dir: Path, args: list[str], env: dict[str, str] | None = None) -> None:
    easyrsa = easy_rsa_dir / "easyrsa"
    if not easyrsa.is_file():
        raise PkiError(f"easyrsa not found: {easyrsa}")
    cmd = [str(easyrsa), "--batch", *args]
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(easy_rsa_dir),
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        raise PkiError("easyrsa timed out") from exc
    except OSError as exc:
        raise PkiError(f"failed to run easyrsa: {exc}") from exc
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()
        raise PkiError(err or f"easyrsa failed ({proc.returncode})")


def issue_client(
    easy_rsa_dir: Path,
    cn: str,
    *,
    days: int = 3650,
) -> CertInfo:
    cn = validate_cn(cn)
    existing = {c.cn: c for c in list_certificates(easy_rsa_dir)}
    if cn in existing and existing[cn].status == "valid":
        raise PkiError(f"client already exists: {cn}")

    import os

    env = os.environ.copy()
    env["EASYRSA_CERT_EXPIRE"] = str(int(days))
    _run_easyrsa(easy_rsa_dir, ["build-client-full", cn, "nopass"], env=env)
    certs = {c.cn: c for c in list_certificates(easy_rsa_dir)}
    if cn not in certs:
        raise PkiError(f"client created but not found in index: {cn}")
    return certs[cn]


def revoke_client(easy_rsa_dir: Path, cn: str, crl_publish: Path) -> CertInfo:
    cn = validate_cn(cn)
    existing = {c.cn: c for c in list_certificates(easy_rsa_dir)}
    if cn not in existing:
        raise PkiError(f"unknown client: {cn}")
    if existing[cn].status == "revoked":
        return existing[cn]

    # Prefer revoke-issued (newer Easy-RSA), fall back to revoke.
    try:
        _run_easyrsa(easy_rsa_dir, ["revoke-issued", cn])
    except PkiError:
        _run_easyrsa(easy_rsa_dir, ["revoke", cn])

    import os

    env = os.environ.copy()
    env.setdefault("EASYRSA_CRL_DAYS", "3650")
    _run_easyrsa(easy_rsa_dir, ["gen-crl"], env=env)

    src = pki_dir(easy_rsa_dir) / "crl.pem"
    if src.is_file():
        crl_publish.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, crl_publish)
        try:
            crl_publish.chmod(0o644)
        except OSError:
            pass

    certs = {c.cn: c for c in list_certificates(easy_rsa_dir)}
    return certs.get(cn, CertInfo(cn=cn, status="revoked"))


def detect_tls_mode(server_conf: Path) -> str:
    """Return tls-crypt-v2 | tls-crypt | tls-auth | none."""
    if not server_conf.is_file():
        return "none"
    text = server_conf.read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or s.startswith(";"):
            continue
        if s.startswith("tls-crypt-v2"):
            return "tls-crypt-v2"
        if s.startswith("tls-crypt"):
            return "tls-crypt"
        if s.startswith("tls-auth"):
            return "tls-auth"
    return "none"


def _extract_cert_body(cert_text: str) -> str:
    lines = cert_text.splitlines()
    out: list[str] = []
    inside = False
    for line in lines:
        if "BEGIN CERTIFICATE" in line:
            inside = True
        if inside:
            out.append(line)
        if "END CERTIFICATE" in line and inside:
            break
    return "\n".join(out)


def build_ovpn(
    *,
    easy_rsa_dir: Path,
    server_dir: Path,
    server_conf: Path,
    client_template: Path,
    cn: str,
    output_dir: Path,
) -> Path:
    cn = validate_cn(cn)
    if not client_template.is_file():
        raise PkiError(f"client template not found: {client_template}")
    cert_file = issued_cert_path(easy_rsa_dir, cn)
    key_file = private_key_path(easy_rsa_dir, cn)
    ca_file = ca_cert_path(easy_rsa_dir)
    if not cert_file.is_file() or not key_file.is_file():
        raise PkiError(f"missing cert/key for {cn}")
    if not ca_file.is_file():
        raise PkiError(f"CA cert not found: {ca_file}")

    parts: list[str] = [
        client_template.read_text(encoding="utf-8", errors="replace").rstrip(),
        "",
        "<ca>",
        ca_file.read_text(encoding="utf-8", errors="replace").strip(),
        "</ca>",
        "",
        "<cert>",
        _extract_cert_body(cert_file.read_text(encoding="utf-8", errors="replace")),
        "</cert>",
        "",
        "<key>",
        key_file.read_text(encoding="utf-8", errors="replace").strip(),
        "</key>",
        "",
    ]

    tls_mode = detect_tls_mode(server_conf)
    if tls_mode == "tls-crypt-v2":
        server_key = server_dir / "tls-crypt-v2.key"
        if not server_key.is_file():
            raise PkiError(f"tls-crypt-v2 server key missing: {server_key}")
        tmp = server_dir / f"tls-crypt-v2-client.{cn}.tmp"
        try:
            proc = subprocess.run(
                [
                    "openvpn",
                    "--tls-crypt-v2",
                    str(server_key),
                    "--genkey",
                    "tls-crypt-v2-client",
                    str(tmp),
                ],
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )
            if proc.returncode != 0 or not tmp.is_file():
                raise PkiError(
                    (proc.stderr or proc.stdout or "tls-crypt-v2-client failed").strip()
                )
            parts.extend(
                [
                    "<tls-crypt-v2>",
                    tmp.read_text(encoding="utf-8", errors="replace").strip(),
                    "</tls-crypt-v2>",
                    "",
                ]
            )
        finally:
            if tmp.exists():
                tmp.unlink()
    elif tls_mode == "tls-crypt":
        key = server_dir / "tls-crypt.key"
        if not key.is_file():
            raise PkiError(f"tls-crypt.key missing: {key}")
        parts.extend(
            [
                "<tls-crypt>",
                key.read_text(encoding="utf-8", errors="replace").strip(),
                "</tls-crypt>",
                "",
            ]
        )
    elif tls_mode == "tls-auth":
        key = server_dir / "tls-auth.key"
        if not key.is_file():
            # older layouts sometimes use ta.key
            alt = server_dir / "ta.key"
            key = alt if alt.is_file() else key
        if not key.is_file():
            raise PkiError(f"tls-auth key missing under {server_dir}")
        parts.extend(
            [
                "key-direction 1",
                "<tls-auth>",
                key.read_text(encoding="utf-8", errors="replace").strip(),
                "</tls-auth>",
                "",
            ]
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    out = output_dir / f"{cn}.ovpn"
    out.write_text("\n".join(parts) + "\n", encoding="utf-8")
    try:
        out.chmod(0o600)
    except OSError:
        pass
    return out
