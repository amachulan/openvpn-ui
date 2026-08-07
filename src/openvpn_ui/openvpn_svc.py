"""OpenVPN systemd service helpers."""

from __future__ import annotations

import shutil
import subprocess
from typing import Any


class OpenVpnServiceError(Exception):
    """systemctl / unit operation failed."""


DEFAULT_CANDIDATES = (
    "openvpn-server@server",
    "openvpn@server",
)


def _systemctl(*args: str, timeout: float = 30) -> subprocess.CompletedProcess[str]:
    binary = shutil.which("systemctl")
    if not binary:
        raise OpenVpnServiceError("systemctl not found")
    try:
        return subprocess.run(
            [binary, *args],
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise OpenVpnServiceError("systemctl timed out") from exc
    except OSError as exc:
        raise OpenVpnServiceError(f"systemctl failed: {exc}") from exc


def resolve_unit(configured: str | None = None) -> str:
    """Return the OpenVPN systemd unit name."""
    if configured and configured.strip():
        return configured.strip()
    for name in DEFAULT_CANDIDATES:
        proc = _systemctl("cat", name, timeout=5)
        if proc.returncode == 0:
            return name
    # Fall back to angristan default even if inactive / missing unit file probe.
    return DEFAULT_CANDIDATES[0]


def service_status(unit: str) -> dict[str, Any]:
    active_proc = _systemctl("is-active", unit, timeout=5)
    enabled_proc = _systemctl("is-enabled", unit, timeout=5)
    active = (active_proc.stdout or "").strip() or "unknown"
    enabled = (enabled_proc.stdout or "").strip() or "unknown"
    show = _systemctl(
        "show",
        unit,
        "--no-page",
        "-p",
        "Id",
        "-p",
        "ActiveState",
        "-p",
        "SubState",
        "-p",
        "MainPID",
        "-p",
        "Description",
        timeout=5,
    )
    props: dict[str, str] = {}
    for line in (show.stdout or "").splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            props[k] = v
    return {
        "unit": unit,
        "active": active,
        "enabled": enabled,
        "running": active == "active",
        "sub_state": props.get("SubState", ""),
        "main_pid": int(props["MainPID"]) if props.get("MainPID", "").isdigit() else 0,
        "description": props.get("Description", ""),
    }


def restart_service(unit: str) -> dict[str, Any]:
    proc = _systemctl("restart", unit, timeout=60)
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()
        raise OpenVpnServiceError(err or f"restart failed ({proc.returncode})")
    status = service_status(unit)
    return {"ok": True, "action": "restart", "status": status}


def reload_service(unit: str) -> dict[str, Any]:
    proc = _systemctl("reload", unit, timeout=60)
    if proc.returncode != 0:
        # Many OpenVPN units only support restart.
        return restart_service(unit)
    status = service_status(unit)
    return {"ok": True, "action": "reload", "status": status}
