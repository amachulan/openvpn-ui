"""High-level vpnctl operations."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import pki
from .catalog import Catalog
from .access import is_loopback_bind, resolve_allow_networks
from .config import (
    load_config,
    normalize_mail_settings,
    normalize_telegram_settings,
    path_from_cfg,
    persist_notify_settings,
    public_notify_settings,
    resolve_management,
    resolve_status_log_path,
)
from .management import ManagementError, OpenVpnManagementClient, SessionNotFoundError
from .notify import NotifyError, send_ovpn_email, send_ovpn_telegram
from .status import OnlineClient, read_online_clients


class VpnctlService:
    def __init__(self, cfg: dict[str, Any] | None = None) -> None:
        self.cfg = cfg or load_config()
        self.catalog = Catalog(path_from_cfg(self.cfg, "catalog_db"))

    @property
    def easy_rsa_dir(self) -> Path:
        return path_from_cfg(self.cfg, "easy_rsa_dir")

    def health(self) -> dict[str, Any]:
        easy = self.easy_rsa_dir
        idx = pki.index_path(easy)
        status_path = resolve_status_log_path(self.cfg)
        mgmt = resolve_management(self.cfg)
        api = self.cfg.get("api") or {}
        host = str(api.get("host") or "0.0.0.0")
        allow_nets = [str(n) for n in resolve_allow_networks(self.cfg)]
        return {
            "ok": True,
            "version": "0.1.2",
            "config_path": self.cfg.get("_config_path"),
            "easy_rsa_dir": str(easy),
            "index_txt": idx.is_file(),
            "status_log": str(status_path),
            "status_log_exists": status_path.is_file(),
            "api": {
                "host": host,
                "port": int(api.get("port") or 8080),
                "loopback_only": is_loopback_bind(host),
                "allow_from": allow_nets,
                "allow_from_vpn": bool(api.get("allow_from_vpn")),
            },
            "management": {
                "mode": mgmt.get("mode"),
                "path": mgmt.get("path"),
                "host": mgmt.get("host"),
                "port": mgmt.get("port"),
            },
        }

    def list_clients(self) -> list[dict[str, Any]]:
        certs = pki.list_certificates(
            self.easy_rsa_dir,
            clients_only=True,
            server_conf=path_from_cfg(self.cfg, "server_conf"),
        )
        meta = self.catalog.all_clients()
        online = {c.cn for c in self.list_sessions()}
        out: list[dict[str, Any]] = []
        for cert in certs:
            row = cert.to_dict()
            m = meta.get(cert.cn)
            row["label"] = m.label if m else ""
            row["notes"] = m.notes if m else ""
            row["email"] = m.email if m else ""
            row["telegram_chat_id"] = m.telegram_chat_id if m else ""
            row["online"] = cert.cn in online
            out.append(row)
        return out

    def update_client_meta(
        self,
        cn: str,
        *,
        label: str | None = None,
        notes: str | None = None,
        email: str | None = None,
        telegram_chat_id: str | None = None,
    ) -> dict[str, Any]:
        cn = pki.validate_cn(cn)
        meta = self.catalog.upsert_client(
            cn,
            label=label,
            notes=notes,
            email=email,
            telegram_chat_id=telegram_chat_id,
        )
        self.catalog.add_event("meta_update", cn=cn, detail="updated labels/notes")
        return meta.to_dict()

    def issue(
        self,
        cn: str,
        *,
        days: int = 3650,
        label: str = "",
        notes: str = "",
        email: str = "",
        telegram_chat_id: str = "",
        deliver_email: bool = False,
        deliver_telegram: bool = False,
    ) -> dict[str, Any]:
        cert = pki.issue_client(self.easy_rsa_dir, cn, days=days)
        ovpn = pki.build_ovpn(
            easy_rsa_dir=self.easy_rsa_dir,
            server_dir=path_from_cfg(self.cfg, "openvpn_server_dir"),
            server_conf=path_from_cfg(self.cfg, "server_conf"),
            client_template=path_from_cfg(self.cfg, "client_template"),
            cn=cert.cn,
            output_dir=path_from_cfg(self.cfg, "client_output_dir"),
        )
        self.catalog.upsert_client(
            cert.cn,
            label=label,
            notes=notes,
            email=email,
            telegram_chat_id=telegram_chat_id,
        )
        self.catalog.add_event(
            "issue",
            cn=cert.cn,
            detail=f"days={days}; ovpn={ovpn}",
        )
        delivery: dict[str, Any] = {}
        meta = self.catalog.get_client(cert.cn)
        if deliver_email:
            to_addr = email or (meta.email if meta else "")
            try:
                send_ovpn_email(
                    self.cfg.get("mail") or {},
                    to_addr=to_addr,
                    cn=cert.cn,
                    ovpn_path=ovpn,
                )
                delivery["email"] = "sent"
                self.catalog.add_event("deliver_email", cn=cert.cn, detail=to_addr)
            except NotifyError as exc:
                delivery["email"] = f"error: {exc}"
        if deliver_telegram:
            chat = telegram_chat_id or (meta.telegram_chat_id if meta else "")
            try:
                send_ovpn_telegram(
                    self.cfg.get("telegram") or {},
                    chat_id=chat,
                    cn=cert.cn,
                    ovpn_path=ovpn,
                )
                delivery["telegram"] = "sent"
                self.catalog.add_event("deliver_telegram", cn=cert.cn, detail=chat)
            except NotifyError as exc:
                delivery["telegram"] = f"error: {exc}"
        result = cert.to_dict()
        result["ovpn_path"] = str(ovpn)
        result["delivery"] = delivery
        return result

    def revoke(self, cn: str, *, disconnect: bool = True) -> dict[str, Any]:
        cert = pki.revoke_client(
            self.easy_rsa_dir,
            cn,
            path_from_cfg(self.cfg, "crl_publish"),
        )
        # Remove delivered profile copy
        ovpn = path_from_cfg(self.cfg, "client_output_dir") / f"{cert.cn}.ovpn"
        if ovpn.is_file():
            try:
                ovpn.unlink()
            except OSError:
                pass
        disconnect_info: dict[str, Any] = {}
        if disconnect:
            try:
                result = self.disconnect(cert.cn)
                disconnect_info = result
            except (SessionNotFoundError, ManagementError) as exc:
                disconnect_info = {"warning": str(exc)}
        self.catalog.add_event("revoke", cn=cert.cn, detail=str(disconnect_info))
        out = cert.to_dict()
        out["disconnect"] = disconnect_info
        return out

    def ovpn_path(self, cn: str) -> Path:
        cn = pki.validate_cn(cn)
        output_dir = path_from_cfg(self.cfg, "client_output_dir")
        existing = pki.find_existing_ovpn(cn, output_dir)
        if existing is not None:
            return existing
        # Rebuild on demand if cert still valid (also covers angristan-issued certs
        # whose .ovpn was deleted from /home but PKI files remain).
        certs = {c.cn: c for c in pki.list_certificates(self.easy_rsa_dir)}
        cert = certs.get(cn)
        if cert is None or cert.status != "valid":
            raise pki.PkiError(f"no active profile for {cn}")
        return pki.build_ovpn(
            easy_rsa_dir=self.easy_rsa_dir,
            server_dir=path_from_cfg(self.cfg, "openvpn_server_dir"),
            server_conf=path_from_cfg(self.cfg, "server_conf"),
            client_template=path_from_cfg(self.cfg, "client_template"),
            cn=cn,
            output_dir=output_dir,
        )

    def list_sessions(self) -> list[OnlineClient]:
        """Prefer status log; only touch management if the log file is missing."""
        status_path = resolve_status_log_path(self.cfg)
        if status_path.is_file():
            return read_online_clients(status_path)
        try:
            endpoint = resolve_management(self.cfg)
            # Keep listing snappy if management is unreachable.
            endpoint = dict(endpoint)
            endpoint["timeout"] = min(float(endpoint.get("timeout") or 15), 2.0)
            return OpenVpnManagementClient(endpoint).list_sessions()
        except ManagementError:
            return []

    def disconnect(
        self,
        cn: str,
        *,
        client_id: str = "",
        real_address: str = "",
    ) -> dict[str, Any]:
        client = OpenVpnManagementClient(resolve_management(self.cfg))
        result = client.disconnect(cn, client_id=client_id, real_address=real_address)
        self.catalog.add_event(
            "disconnect",
            cn=cn,
            detail=f"{result.method}: {result.message}",
        )
        return {
            "method": result.method,
            "message": result.message,
            "client_id": result.client_id,
        }

    def expiry_warnings(self) -> list[dict[str, Any]]:
        warn_days = int((self.cfg.get("expiry") or {}).get("warn_days") or 30)
        out: list[dict[str, Any]] = []
        for cert in pki.list_certificates(
            self.easy_rsa_dir,
            clients_only=True,
            server_conf=path_from_cfg(self.cfg, "server_conf"),
        ):
            if cert.status != "valid":
                continue
            if cert.days_remaining is None:
                continue
            if cert.days_remaining <= warn_days:
                row = cert.to_dict()
                row["warn_days"] = warn_days
                out.append(row)
        out.sort(key=lambda r: (r.get("days_remaining") is None, r.get("days_remaining")))
        return out

    def audit(self, limit: int = 100) -> list[dict[str, Any]]:
        return [e.to_dict() for e in self.catalog.list_events(limit=limit)]

    def get_notify_settings(self) -> dict[str, Any]:
        return public_notify_settings(self.cfg)

    def update_notify_settings(
        self,
        *,
        mail: dict[str, Any] | None = None,
        telegram: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        next_mail = normalize_mail_settings(
            mail if mail is not None else (self.cfg.get("mail") or {}),
            self.cfg.get("mail") or {},
        )
        next_tg = normalize_telegram_settings(
            telegram if telegram is not None else (self.cfg.get("telegram") or {}),
            self.cfg.get("telegram") or {},
        )
        persist_notify_settings(self.cfg, mail=next_mail, telegram=next_tg)
        parts: list[str] = []
        if mail is not None:
            parts.append("mail")
        if telegram is not None:
            parts.append("telegram")
        self.catalog.add_event(
            "settings_update",
            cn="",
            detail=",".join(parts) or "notify",
        )
        return public_notify_settings(self.cfg)

    def deliver(
        self,
        cn: str,
        *,
        via: str,
        email: str = "",
        telegram_chat_id: str = "",
    ) -> dict[str, Any]:
        ovpn = self.ovpn_path(cn)
        meta = self.catalog.get_client(cn)
        if via == "email":
            to_addr = email or (meta.email if meta else "")
            send_ovpn_email(self.cfg.get("mail") or {}, to_addr=to_addr, cn=cn, ovpn_path=ovpn)
            self.catalog.add_event("deliver_email", cn=cn, detail=to_addr)
            return {"via": "email", "to": to_addr}
        if via == "telegram":
            chat = telegram_chat_id or (meta.telegram_chat_id if meta else "")
            send_ovpn_telegram(
                self.cfg.get("telegram") or {},
                chat_id=chat,
                cn=cn,
                ovpn_path=ovpn,
            )
            self.catalog.add_event("deliver_telegram", cn=cn, detail=chat)
            return {"via": "telegram", "chat_id": chat}
        raise NotifyError(f"unsupported delivery channel: {via}")
