"""OpenVPN management interface client (Unix socket or TCP)."""

from __future__ import annotations

import socket
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Iterator

from .status import OnlineClient, parse_openvpn_status


class ManagementError(Exception):
    """Management socket or command failure."""


class SessionNotFoundError(ManagementError):
    """No matching live session."""


@dataclass
class DisconnectResult:
    method: str
    message: str
    client_id: str = ""


class OpenVpnManagementClient:
    def __init__(self, endpoint: dict[str, Any]) -> None:
        self.endpoint = endpoint
        self.timeout = float(endpoint.get("timeout") or 15)

    @contextmanager
    def _connection(self) -> Iterator[tuple[socket.socket, Any]]:
        mode = self.endpoint.get("mode")
        try:
            if mode == "unix":
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                sock.settimeout(self.timeout)
                sock.connect(str(self.endpoint["path"]))
            else:
                sock = socket.create_connection(
                    (str(self.endpoint["host"]), int(self.endpoint["port"])),
                    timeout=self.timeout,
                )
                sock.settimeout(self.timeout)
        except OSError as exc:
            raise ManagementError(f"management connect failed: {exc}") from exc
        reader = sock.makefile("r", encoding="utf-8", errors="replace", newline="\n")
        try:
            yield sock, reader
        finally:
            try:
                reader.close()
            finally:
                sock.close()

    def _read_line(self, reader: Any) -> str:
        try:
            line = reader.readline()
        except (OSError, TimeoutError, socket.timeout) as exc:
            raise ManagementError(f"management: {exc}") from exc
        if line == "":
            raise ManagementError("management: connection closed")
        return line.rstrip("\r\n")

    def _send(self, sock: socket.socket, command: str) -> None:
        try:
            sock.sendall((command.strip() + "\n").encode("utf-8"))
        except OSError as exc:
            raise ManagementError(f"management: {exc}") from exc

    def _consume_greeting(self, reader: Any) -> None:
        line = self._read_line(reader)
        if line.startswith(">PASSWORD:"):
            raise ManagementError("management requires password (unsupported)")
        if not line.startswith(">"):
            raise ManagementError(f"unexpected greeting: {line}")

    def _read_until_end(self, reader: Any) -> list[str]:
        lines: list[str] = []
        while True:
            line = self._read_line(reader)
            if line.startswith("ERROR:"):
                raise ManagementError(line)
            if line == "END":
                break
            lines.append(line)
        return lines

    def _read_success(self, reader: Any, *, max_lines: int = 200) -> str:
        for _ in range(max_lines):
            line = self._read_line(reader)
            if line.startswith(">"):
                continue
            if line.startswith("ERROR:"):
                raise ManagementError(line)
            if line.startswith("SUCCESS:"):
                return line
        raise ManagementError("management: no SUCCESS/ERROR")

    def fetch_status_text(self) -> str:
        last_err: ManagementError | None = None
        for command in ("status 3", "status 2", "status"):
            try:
                with self._connection() as (sock, reader):
                    self._consume_greeting(reader)
                    self._send(sock, command)
                    lines = self._read_until_end(reader)
                    try:
                        self._read_success(reader)
                    except ManagementError:
                        pass
                    self._send(sock, "quit")
                    return "\n".join(lines) + "\nEND\n"
            except ManagementError as exc:
                last_err = exc
                continue
        if last_err:
            raise last_err
        return ""

    def list_sessions(self) -> list[OnlineClient]:
        text = self.fetch_status_text()
        return parse_openvpn_status(text)

    def disconnect(
        self,
        cn: str,
        *,
        client_id: str = "",
        real_address: str = "",
    ) -> DisconnectResult:
        cn = (cn or "").strip()
        if not cn:
            raise ManagementError("client name is required")

        if client_id:
            try:
                return self._client_kill(client_id, cn)
            except (SessionNotFoundError, ManagementError):
                pass

        if real_address:
            sessions = self.list_sessions()
            matches = [
                s
                for s in sessions
                if s.cn == cn
                and s.real_address.lower() == real_address.strip().lower()
            ]
            if len(matches) == 1 and matches[0].client_id:
                return self._client_kill(matches[0].client_id, cn)

        return self._kill_cn(cn)

    def _client_kill(self, client_id: str, cn: str) -> DisconnectResult:
        with self._connection() as (sock, reader):
            self._consume_greeting(reader)
            self._send(sock, f"client-kill {client_id}")
            try:
                message = self._read_success(reader)
            except ManagementError as exc:
                text = str(exc).lower()
                if "not found" in text or "unable" in text:
                    raise SessionNotFoundError(f"no session for {cn}") from exc
                raise
            try:
                self._send(sock, "quit")
            except OSError:
                pass
        return DisconnectResult(method="client-kill", message=message, client_id=client_id)

    def _kill_cn(self, cn: str) -> DisconnectResult:
        with self._connection() as (sock, reader):
            self._consume_greeting(reader)
            self._send(sock, f"kill {cn}")
            try:
                message = self._read_success(reader)
            except ManagementError as exc:
                text = str(exc).lower()
                if "not found" in text or "unable" in text:
                    raise SessionNotFoundError(f"no session for {cn}") from exc
                raise
            try:
                self._send(sock, "quit")
            except OSError:
                pass
        return DisconnectResult(method="kill", message=message)
