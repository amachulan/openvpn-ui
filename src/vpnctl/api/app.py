"""FastAPI application for vpnctl."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware

from vpnctl import __version__
from vpnctl.access import client_ip_allowed, extract_client_ip, resolve_allow_networks
from vpnctl.api.auth import require_token
from vpnctl.config import load_config
from vpnctl.management import ManagementError, SessionNotFoundError
from vpnctl.notify import NotifyError
from vpnctl.pki import PkiError
from vpnctl.service import VpnctlService

WEB_DIR = Path(__file__).resolve().parent.parent / "web"


class AllowFromMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: Any, networks: list[Any]) -> None:
        super().__init__(app)
        self.networks = networks

    async def dispatch(self, request: Request, call_next: Any) -> Any:
        if not self.networks:
            return await call_next(request)
        client_host = request.client.host if request.client else ""
        ip = extract_client_ip(dict(request.headers), client_host)
        if not client_ip_allowed(ip, self.networks):
            return JSONResponse(
                status_code=403,
                content={"detail": f"client IP not allowed: {ip or 'unknown'}"},
            )
        return await call_next(request)


class IssueBody(BaseModel):
    cn: str = Field(..., min_length=1, max_length=64)
    days: int = Field(3650, ge=1, le=36500)
    label: str = ""
    notes: str = ""
    email: str = ""
    telegram_chat_id: str = ""
    deliver_email: bool = False
    deliver_telegram: bool = False


class MetaBody(BaseModel):
    label: str | None = None
    notes: str | None = None
    email: str | None = None
    telegram_chat_id: str | None = None


class DisconnectBody(BaseModel):
    cn: str
    client_id: str = ""
    real_address: str = ""


class DeliverBody(BaseModel):
    via: str = Field(..., pattern="^(email|telegram)$")
    email: str = ""
    telegram_chat_id: str = ""


def create_app(cfg: dict[str, Any] | None = None) -> FastAPI:
    cfg = cfg or load_config()
    service = VpnctlService(cfg)
    auth = require_token(cfg)
    allow_networks = resolve_allow_networks(cfg)

    app = FastAPI(
        title="vpnctl",
        version=__version__,
        description="Web UI/API for OpenVPN Community (angristan-compatible)",
    )
    if allow_networks:
        app.add_middleware(AllowFromMiddleware, networks=allow_networks)

    @app.get("/api/v1/health")
    def health() -> dict[str, Any]:
        return service.health()

    @app.get("/api/v1/clients")
    def clients(_: str = Depends(auth)) -> list[dict[str, Any]]:
        return service.list_clients()

    @app.post("/api/v1/clients")
    def issue(body: IssueBody, _: str = Depends(auth)) -> dict[str, Any]:
        try:
            return service.issue(
                body.cn,
                days=body.days,
                label=body.label,
                notes=body.notes,
                email=body.email,
                telegram_chat_id=body.telegram_chat_id,
                deliver_email=body.deliver_email,
                deliver_telegram=body.deliver_telegram,
            )
        except PkiError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.patch("/api/v1/clients/{cn}")
    def patch_meta(cn: str, body: MetaBody, _: str = Depends(auth)) -> dict[str, Any]:
        try:
            return service.update_client_meta(
                cn,
                label=body.label,
                notes=body.notes,
                email=body.email,
                telegram_chat_id=body.telegram_chat_id,
            )
        except PkiError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/clients/{cn}/revoke")
    def revoke(cn: str, _: str = Depends(auth)) -> dict[str, Any]:
        try:
            return service.revoke(cn)
        except PkiError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/v1/clients/{cn}/ovpn")
    def download_ovpn(cn: str, _: str = Depends(auth)) -> FileResponse:
        try:
            path = service.ovpn_path(cn)
        except PkiError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return FileResponse(
            path,
            media_type="application/x-openvpn-profile",
            filename=f"{cn}.ovpn",
        )

    @app.post("/api/v1/clients/{cn}/deliver")
    def deliver(cn: str, body: DeliverBody, _: str = Depends(auth)) -> dict[str, Any]:
        try:
            return service.deliver(
                cn,
                via=body.via,
                email=body.email,
                telegram_chat_id=body.telegram_chat_id,
            )
        except (PkiError, NotifyError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/v1/sessions")
    def sessions(_: str = Depends(auth)) -> list[dict[str, Any]]:
        return [s.to_dict() for s in service.list_sessions()]

    @app.post("/api/v1/sessions/disconnect")
    def disconnect(body: DisconnectBody, _: str = Depends(auth)) -> dict[str, Any]:
        try:
            return service.disconnect(
                body.cn,
                client_id=body.client_id,
                real_address=body.real_address,
            )
        except SessionNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ManagementError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    @app.get("/api/v1/expiry")
    def expiry(_: str = Depends(auth)) -> list[dict[str, Any]]:
        return service.expiry_warnings()

    @app.get("/api/v1/audit")
    def audit(
        limit: int = Query(100, ge=1, le=1000),
        _: str = Depends(auth),
    ) -> list[dict[str, Any]]:
        return service.audit(limit=limit)

    if WEB_DIR.is_dir():
        app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")

        @app.get("/", response_class=HTMLResponse)
        def index() -> HTMLResponse:
            index_path = WEB_DIR / "index.html"
            return HTMLResponse(index_path.read_text(encoding="utf-8"))

    return app


# ASGI entry for `uvicorn vpnctl.api.app:app`
app = create_app()
