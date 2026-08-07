"""SQLite catalog for labels, notes, and audit events (not PKI source of truth)."""

from __future__ import annotations

import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass
class ClientMeta:
    cn: str
    label: str = ""
    notes: str = ""
    email: str = ""
    telegram_chat_id: str = ""
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AuditEvent:
    id: int
    ts: str
    action: str
    cn: str
    detail: str = ""
    actor: str = "api"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class Catalog:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS clients (
                    cn TEXT PRIMARY KEY,
                    label TEXT NOT NULL DEFAULT '',
                    notes TEXT NOT NULL DEFAULT '',
                    email TEXT NOT NULL DEFAULT '',
                    telegram_chat_id TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT NOT NULL,
                    action TEXT NOT NULL,
                    cn TEXT NOT NULL DEFAULT '',
                    detail TEXT NOT NULL DEFAULT '',
                    actor TEXT NOT NULL DEFAULT 'api'
                );
                CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts DESC);
                """
            )

    def upsert_client(
        self,
        cn: str,
        *,
        label: str | None = None,
        notes: str | None = None,
        email: str | None = None,
        telegram_chat_id: str | None = None,
    ) -> ClientMeta:
        now = _utc_now()
        existing = self.get_client(cn)
        if existing is None:
            meta = ClientMeta(
                cn=cn,
                label=label or "",
                notes=notes or "",
                email=email or "",
                telegram_chat_id=telegram_chat_id or "",
                created_at=now,
                updated_at=now,
            )
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO clients
                    (cn, label, notes, email, telegram_chat_id, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        meta.cn,
                        meta.label,
                        meta.notes,
                        meta.email,
                        meta.telegram_chat_id,
                        meta.created_at,
                        meta.updated_at,
                    ),
                )
            return meta

        meta = ClientMeta(
            cn=cn,
            label=existing.label if label is None else label,
            notes=existing.notes if notes is None else notes,
            email=existing.email if email is None else email,
            telegram_chat_id=(
                existing.telegram_chat_id
                if telegram_chat_id is None
                else telegram_chat_id
            ),
            created_at=existing.created_at,
            updated_at=now,
        )
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE clients
                SET label=?, notes=?, email=?, telegram_chat_id=?, updated_at=?
                WHERE cn=?
                """,
                (
                    meta.label,
                    meta.notes,
                    meta.email,
                    meta.telegram_chat_id,
                    meta.updated_at,
                    cn,
                ),
            )
        return meta

    def get_client(self, cn: str) -> ClientMeta | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM clients WHERE cn = ?", (cn,)
            ).fetchone()
        if row is None:
            return None
        return ClientMeta(**dict(row))

    def all_clients(self) -> dict[str, ClientMeta]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM clients").fetchall()
        return {row["cn"]: ClientMeta(**dict(row)) for row in rows}

    def delete_client(self, cn: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM clients WHERE cn = ?", (cn,))

    def add_event(
        self,
        action: str,
        cn: str = "",
        detail: str = "",
        actor: str = "api",
    ) -> AuditEvent:
        ts = _utc_now()
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO events (ts, action, cn, detail, actor)
                VALUES (?, ?, ?, ?, ?)
                """,
                (ts, action, cn, detail, actor),
            )
            event_id = int(cur.lastrowid)
        return AuditEvent(
            id=event_id, ts=ts, action=action, cn=cn, detail=detail, actor=actor
        )

    def list_events(self, *, limit: int = 100) -> list[AuditEvent]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, ts, action, cn, detail, actor
                FROM events
                ORDER BY id DESC
                LIMIT ?
                """,
                (int(limit),),
            ).fetchall()
        return [AuditEvent(**dict(row)) for row in rows]
