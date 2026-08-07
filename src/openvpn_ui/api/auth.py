"""Simple bearer-token auth for the API."""

from __future__ import annotations

import secrets
from typing import Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

_bearer = HTTPBearer(auto_error=False)


def require_token(cfg: dict[str, Any]):
    expected = str((cfg.get("api") or {}).get("token") or "")

    async def _dep(
        request: Request,
        credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    ) -> str:
        provided = ""
        if credentials and credentials.scheme.lower() == "bearer":
            provided = credentials.credentials or ""
        if not provided:
            provided = request.headers.get("X-API-Token", "").strip()
        if not expected or expected == "change-me":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="API token is not configured (set api.token in config)",
            )
        if not provided or not secrets.compare_digest(provided, expected):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid or missing API token",
            )
        return provided

    return _dep
