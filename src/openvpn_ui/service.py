"""High-level openvpn-ui operations."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import pki
from . import __version__
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
from . import openvpn_svc
from . import server_conf
from .instances import (
    INSTANCE_IDS,
    enabled_instance_ids,
    get_instance,
    normalize_listen_proto,
    persist_instances,
    primary_instance_id,
    resolve_instances,
)
from .status import OnlineClient, read_online_clients


class OpenVpnUiService:
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
            "version": __version__,
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
            row["profiles"] = enabled_instance_ids(self.cfg) or [
                primary_instance_id(self.cfg)
            ]
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
        ovpn_paths = self._build_client_profiles(cert.cn)
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
            detail=f"days={days}; ovpn={','.join(str(p) for p in ovpn_paths)}",
        )
        delivery: dict[str, Any] = {}
        meta = self.catalog.get_client(cert.cn)
        primary_ovpn = ovpn_paths[0]
        if deliver_email:
            to_addr = email or (meta.email if meta else "")
            try:
                send_ovpn_email(
                    self.cfg.get("mail") or {},
                    to_addr=to_addr,
                    cn=cert.cn,
                    ovpn_paths=ovpn_paths,
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
                    ovpn_paths=ovpn_paths,
                )
                delivery["telegram"] = "sent"
                self.catalog.add_event("deliver_telegram", cn=cert.cn, detail=chat)
            except NotifyError as exc:
                delivery["telegram"] = f"error: {exc}"
        result = cert.to_dict()
        result["ovpn_path"] = str(primary_ovpn)
        result["ovpn_paths"] = [str(p) for p in ovpn_paths]
        result["delivery"] = delivery
        return result

    def revoke(self, cn: str, *, disconnect: bool = True) -> dict[str, Any]:
        cert = pki.revoke_client(
            self.easy_rsa_dir,
            cn,
            path_from_cfg(self.cfg, "crl_publish"),
        )
        # Remove delivered profile copies
        out_dir = path_from_cfg(self.cfg, "client_output_dir")
        for path in out_dir.glob(f"{cert.cn}*.ovpn"):
            try:
                path.unlink()
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

    def renew(self, cn: str, *, days: int = 3650) -> dict[str, Any]:
        cert = pki.renew_client(
            self.easy_rsa_dir,
            cn,
            path_from_cfg(self.cfg, "crl_publish"),
            days=days,
        )
        ovpn_paths = self._build_client_profiles(cert.cn)
        self.catalog.add_event("client_renew", cn=cert.cn, detail=f"days={days}")
        result = cert.to_dict()
        result["ovpn_path"] = str(ovpn_paths[0])
        result["ovpn_paths"] = [str(p) for p in ovpn_paths]
        return result

    def ovpn_path(self, cn: str, *, proto: str | None = None) -> Path:
        cn = pki.validate_cn(cn)
        family = (proto or primary_instance_id(self.cfg)).strip().lower()
        if family not in INSTANCE_IDS:
            raise pki.PkiError(f"unknown proto: {proto}")
        inst = get_instance(self.cfg, family)
        if not inst.get("enabled"):
            raise pki.PkiError(f"{family} instance is not enabled")
        # Always rebuild so port/proto/crypto match current instance settings.
        paths = self._build_client_profiles(cn)
        for path in paths:
            if path.name.endswith(f"-{family}.ovpn") or (
                family == primary_instance_id(self.cfg) and path.name == f"{cn}.ovpn"
            ):
                return path
        raise pki.PkiError(f"no {family} profile for {cn}")

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
        ovpn_paths = self._build_client_profiles(cn)
        meta = self.catalog.get_client(cn)
        if via == "email":
            to_addr = email or (meta.email if meta else "")
            send_ovpn_email(
                self.cfg.get("mail") or {},
                to_addr=to_addr,
                cn=cn,
                ovpn_paths=ovpn_paths,
            )
            self.catalog.add_event("deliver_email", cn=cn, detail=to_addr)
            return {"via": "email", "to": to_addr, "files": [p.name for p in ovpn_paths]}
        if via == "telegram":
            chat = telegram_chat_id or (meta.telegram_chat_id if meta else "")
            send_ovpn_telegram(
                self.cfg.get("telegram") or {},
                chat_id=chat,
                cn=cn,
                ovpn_paths=ovpn_paths,
            )
            self.catalog.add_event("deliver_telegram", cn=cn, detail=chat)
            return {
                "via": "telegram",
                "chat_id": chat,
                "files": [p.name for p in ovpn_paths],
            }
        raise NotifyError(f"unsupported delivery channel: {via}")

    def _backup_dir(self) -> Path:
        try:
            return path_from_cfg(self.cfg, "server_conf_backup_dir")
        except KeyError:
            return Path("/var/lib/openvpn-ui/backups")

    def _instance_listen(self, instance_id: str) -> tuple[str, int, Path]:
        inst = get_instance(self.cfg, instance_id)
        conf_path = Path(str(inst["conf"]))
        port = int(inst.get("port") or (443 if instance_id == "tcp" else 1194))
        proto = normalize_listen_proto(instance_id, None)
        if conf_path.is_file():
            _, settings = server_conf.read_server_conf(conf_path)
            if settings.port:
                port = int(settings.port)
            if settings.proto:
                proto = normalize_listen_proto(instance_id, settings.proto)
        return proto, port, conf_path

    def _client_endpoint(self, instance_id: str) -> tuple[str, int, str | None]:
        """Proto/port/host written into client .ovpn (NAT-aware)."""
        inst = get_instance(self.cfg, instance_id)
        proto, listen_port, _ = self._instance_listen(instance_id)
        host = str(inst.get("external_host") or "").strip() or None
        ep = inst.get("external_port")
        port = int(ep) if ep not in (None, "", 0, "0") else listen_port
        return proto, port, host

    def _build_client_profiles(self, cn: str) -> list[Path]:
        certs = {c.cn: c for c in pki.list_certificates(self.easy_rsa_dir)}
        cert = certs.get(cn)
        if cert is None or cert.status != "valid":
            raise pki.PkiError(f"no active profile for {cn}")
        enabled = enabled_instance_ids(self.cfg)
        if not enabled:
            enabled = [primary_instance_id(self.cfg)]
        paths: list[Path] = []
        primary = primary_instance_id(self.cfg)
        # Prefer primary conf for tls mode detection.
        primary_conf = Path(str(get_instance(self.cfg, primary)["conf"]))
        if not primary_conf.is_file():
            primary_conf = path_from_cfg(self.cfg, "server_conf")
        for iid in enabled:
            proto, port, host = self._client_endpoint(iid)
            paths.append(
                pki.build_ovpn(
                    easy_rsa_dir=self.easy_rsa_dir,
                    server_dir=path_from_cfg(self.cfg, "openvpn_server_dir"),
                    server_conf=primary_conf,
                    client_template=path_from_cfg(self.cfg, "client_template"),
                    cn=cn,
                    output_dir=path_from_cfg(self.cfg, "client_output_dir"),
                    proto=proto,
                    port=port,
                    host=host,
                    filename_suffix=iid,
                )
            )
        return paths

    def _instance_unit_status(self, unit: str) -> dict[str, Any]:
        try:
            return openvpn_svc.service_status(unit)
        except openvpn_svc.OpenVpnServiceError as exc:
            return {
                "unit": unit,
                "active": "unknown",
                "enabled": "unknown",
                "running": False,
                "error": str(exc),
            }

    def get_server(self) -> dict[str, Any]:
        instances = resolve_instances(self.cfg)
        out_instances: dict[str, Any] = {}
        for iid, row in instances.items():
            conf_path = Path(str(row["conf"]))
            entry: dict[str, Any] = {
                "id": iid,
                "enabled": bool(row.get("enabled")),
                "primary": bool(row.get("primary")),
                "conf": str(conf_path),
                "service": str(row.get("service") or ""),
                "port": int(row.get("port") or 0),
                "external_host": str(row.get("external_host") or ""),
                "external_port": row.get("external_port"),
                "service_status": self._instance_unit_status(str(row.get("service") or "")),
                "settings": None,
                "conf_exists": conf_path.is_file(),
            }
            if conf_path.is_file():
                _, settings = server_conf.read_server_conf(conf_path)
                entry["settings"] = settings.to_dict()
                entry["port"] = settings.port or entry["port"]
            out_instances[iid] = entry
        return {
            "primary": primary_instance_id(self.cfg),
            "instances": out_instances,
            "paths": {
                "client_template": str(path_from_cfg(self.cfg, "client_template")),
                "backup_dir": str(self._backup_dir()),
            },
            "hint": (
                "UDP and TCP share PKI/CCD and the same VPN subnet. "
                "Do not connect both profiles at once with one CN. "
                "Open the firewall for the secondary port."
            ),
        }

    def update_instance(
        self,
        instance_id: str,
        patch: dict[str, Any],
        *,
        restart: bool = False,
    ) -> dict[str, Any]:
        inst = get_instance(self.cfg, instance_id)
        if not inst.get("enabled"):
            raise server_conf.ServerConfError(f"{instance_id} instance is disabled")
        patch = dict(patch)
        endpoint_keys: list[str] = []
        instances = resolve_instances(self.cfg)
        if "external_host" in patch:
            instances[instance_id]["external_host"] = str(
                patch.pop("external_host") or ""
            ).strip()
            endpoint_keys.append("external_host")
        if "external_port" in patch:
            raw_ep = patch.pop("external_port")
            if raw_ep in (None, "", 0, "0"):
                instances[instance_id]["external_port"] = None
            else:
                ep = int(raw_ep)
                if ep < 1 or ep > 65535:
                    raise server_conf.ServerConfError("external_port must be 1–65535")
                instances[instance_id]["external_port"] = ep
            endpoint_keys.append("external_port")

        conf_path = Path(str(inst["conf"]))
        text, _ = server_conf.read_server_conf(conf_path)
        clean = server_conf.validate_settings_patch(patch) if patch else {}
        if not clean and not endpoint_keys:
            raise server_conf.ServerConfError("no settings to update")
        backup = None
        if clean:
            # Keep instance family: force proto family if proto set.
            if "proto" in clean:
                clean["proto"] = normalize_listen_proto(instance_id, clean["proto"])
            new_text = server_conf.apply_settings_patch(text, clean)
            backup = server_conf.write_server_conf(conf_path, new_text, self._backup_dir())
            if "port" in clean:
                instances[instance_id]["port"] = int(clean["port"])

        if clean or endpoint_keys:
            persist_instances(self.cfg, instances)

        # Sync shared client template only for primary (client-facing endpoint).
        template_changed = False
        if inst.get("primary"):
            client_proto, client_port, client_host = self._client_endpoint(instance_id)
            template_changed = server_conf.sync_client_template(
                path_from_cfg(self.cfg, "client_template"),
                port=client_port,
                proto=client_proto if "proto" in clean else None,
                host=client_host,
            )
        detail_keys = sorted(set(clean.keys()) | set(endpoint_keys))
        detail = f"{instance_id}:" + ",".join(detail_keys)
        if template_changed:
            detail += ";template"
        self.catalog.add_event("server_conf_update", cn="", detail=detail)
        result = self.get_server()
        result["backup"] = str(backup) if backup else ""
        if restart:
            result["restart"] = self.restart_instance(instance_id)
        return result

    def get_instance_conf_raw(self, instance_id: str) -> dict[str, Any]:
        inst = get_instance(self.cfg, instance_id)
        conf_path = Path(str(inst["conf"]))
        text, _ = server_conf.read_server_conf(conf_path)
        return {"id": instance_id, "path": str(conf_path), "content": text}

    def put_instance_conf_raw(
        self, instance_id: str, content: str, *, restart: bool = False
    ) -> dict[str, Any]:
        if not (content or "").strip():
            raise server_conf.ServerConfError("server.conf cannot be empty")
        inst = get_instance(self.cfg, instance_id)
        if not inst.get("enabled") and not Path(str(inst["conf"])).is_file():
            raise server_conf.ServerConfError(f"{instance_id} instance is disabled")
        conf_path = Path(str(inst["conf"]))
        backup = server_conf.write_server_conf(conf_path, content, self._backup_dir())
        self.catalog.add_event("server_conf_update", cn="", detail=f"{instance_id}:raw")
        result: dict[str, Any] = {
            "ok": True,
            "backup": str(backup) if backup else "",
            "path": str(conf_path),
        }
        if restart:
            result["restart"] = self.restart_instance(instance_id)
        return result

    def enable_instance(self, instance_id: str) -> dict[str, Any]:
        instances = resolve_instances(self.cfg)
        inst = instances[instance_id]
        if inst.get("enabled") and Path(str(inst["conf"])).is_file():
            # Still ensure unit is up.
            openvpn_svc.enable_now(str(inst["service"]))
            return self.get_server()
        primary_id = primary_instance_id(self.cfg)
        if instance_id == primary_id:
            raise server_conf.ServerConfError("primary instance is already the base conf")
        primary = instances[primary_id]
        src = Path(str(primary["conf"]))
        if not src.is_file():
            raise server_conf.ServerConfError("primary server.conf not found")
        src_text = src.read_text(encoding="utf-8", errors="replace")
        port = int(inst.get("port") or (443 if instance_id == "tcp" else 1194))
        proto = normalize_listen_proto(instance_id, None)
        cloned = server_conf.clone_instance_conf(
            src_text, instance_id=instance_id, proto=proto, port=port
        )
        dst = Path(str(inst["conf"]))
        server_conf.write_server_conf(dst, cloned, self._backup_dir())
        openvpn_svc.enable_now(str(inst["service"]))
        instances[instance_id]["enabled"] = True
        persist_instances(self.cfg, instances)
        self.catalog.add_event("server_enable", cn="", detail=instance_id)
        return self.get_server()

    def disable_instance(self, instance_id: str) -> dict[str, Any]:
        instances = resolve_instances(self.cfg)
        inst = instances[instance_id]
        if inst.get("primary"):
            raise server_conf.ServerConfError("cannot disable primary instance")
        openvpn_svc.disable_now(str(inst["service"]))
        instances[instance_id]["enabled"] = False
        persist_instances(self.cfg, instances)
        self.catalog.add_event("server_disable", cn="", detail=instance_id)
        return self.get_server()

    def list_instance_backups(self, instance_id: str) -> list[dict[str, Any]]:
        inst = get_instance(self.cfg, instance_id)
        prefix = Path(str(inst["conf"])).name
        return server_conf.list_backups(self._backup_dir(), prefix=prefix)

    def restore_instance_backup(
        self, instance_id: str, backup_id: str, *, restart: bool = False
    ) -> dict[str, Any]:
        inst = get_instance(self.cfg, instance_id)
        conf_path = Path(str(inst["conf"]))
        server_conf.restore_backup(self._backup_dir(), backup_id, conf_path)
        self.catalog.add_event(
            "server_restore", cn="", detail=f"{instance_id}:{backup_id}"
        )
        result: dict[str, Any] = {"ok": True, "restored": backup_id}
        if restart and inst.get("enabled"):
            result["restart"] = self.restart_instance(instance_id)
        result["server"] = self.get_server()
        return result

    def restart_instance(self, instance_id: str) -> dict[str, Any]:
        inst = get_instance(self.cfg, instance_id)
        unit = str(inst.get("service") or "")
        try:
            result = openvpn_svc.restart_service(unit)
        except openvpn_svc.OpenVpnServiceError as exc:
            self.catalog.add_event(
                "server_restart", cn="", detail=f"{instance_id} error: {exc}"
            )
            raise
        self.catalog.add_event("server_restart", cn="", detail=f"{instance_id}:{unit}")
        return result

    # --- Legacy wrappers (primary instance) ---

    def update_server(self, patch: dict[str, Any], *, restart: bool = False) -> dict[str, Any]:
        return self.update_instance(primary_instance_id(self.cfg), patch, restart=restart)

    def get_server_conf_raw(self) -> dict[str, Any]:
        return self.get_instance_conf_raw(primary_instance_id(self.cfg))

    def put_server_conf_raw(self, content: str, *, restart: bool = False) -> dict[str, Any]:
        return self.put_instance_conf_raw(
            primary_instance_id(self.cfg), content, restart=restart
        )

    def list_server_backups(self) -> list[dict[str, Any]]:
        return self.list_instance_backups(primary_instance_id(self.cfg))

    def restore_server_backup(
        self, backup_id: str, *, restart: bool = False
    ) -> dict[str, Any]:
        return self.restore_instance_backup(
            primary_instance_id(self.cfg), backup_id, restart=restart
        )

    def restart_openvpn(self) -> dict[str, Any]:
        return self.restart_instance(primary_instance_id(self.cfg))
