"""Optional email / Telegram delivery of .ovpn profiles."""

from __future__ import annotations

import json
import smtplib
import ssl
import urllib.error
import urllib.request
from email.message import EmailMessage
from pathlib import Path
from typing import Any


class NotifyError(Exception):
    """Delivery failed."""


def send_ovpn_email(
    mail_cfg: dict[str, Any],
    *,
    to_addr: str,
    cn: str,
    ovpn_path: Path,
) -> None:
    if not mail_cfg.get("enabled"):
        raise NotifyError("mail delivery is disabled")
    to_addr = (to_addr or "").strip()
    if not to_addr:
        raise NotifyError("email address is required")
    if not ovpn_path.is_file():
        raise NotifyError(f"profile not found: {ovpn_path}")

    msg = EmailMessage()
    msg["Subject"] = str(mail_cfg.get("subject") or "Your OpenVPN profile")
    msg["From"] = str(mail_cfg.get("from_addr") or "vpnctl@localhost")
    msg["To"] = to_addr
    msg.set_content(
        f"Attached is your OpenVPN profile for client '{cn}'.\n"
        "Import the .ovpn file into your OpenVPN client.\n"
    )
    msg.add_attachment(
        ovpn_path.read_bytes(),
        maintype="application",
        subtype="x-openvpn-profile",
        filename=f"{cn}.ovpn",
    )

    host = str(mail_cfg.get("smtp_host") or "localhost")
    port = int(mail_cfg.get("smtp_port") or 25)
    user = str(mail_cfg.get("smtp_user") or "")
    password = str(mail_cfg.get("smtp_password") or "")
    use_tls = bool(mail_cfg.get("use_tls"))

    try:
        if use_tls:
            context = ssl.create_default_context()
            with smtplib.SMTP(host, port, timeout=30) as smtp:
                smtp.starttls(context=context)
                if user:
                    smtp.login(user, password)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=30) as smtp:
                if user:
                    smtp.login(user, password)
                smtp.send_message(msg)
    except (OSError, smtplib.SMTPException) as exc:
        raise NotifyError(f"SMTP failed: {exc}") from exc


def send_ovpn_telegram(
    tg_cfg: dict[str, Any],
    *,
    chat_id: str,
    cn: str,
    ovpn_path: Path,
) -> None:
    if not tg_cfg.get("enabled"):
        raise NotifyError("telegram delivery is disabled")
    token = str(tg_cfg.get("bot_token") or "").strip()
    chat_id = (chat_id or str(tg_cfg.get("chat_id") or "")).strip()
    if not token:
        raise NotifyError("telegram bot_token is not configured")
    if not chat_id:
        raise NotifyError("telegram chat_id is required")
    if not ovpn_path.is_file():
        raise NotifyError(f"profile not found: {ovpn_path}")

    boundary = "----vpnctlBoundary7MA4YWxkTrZu0gW"
    caption = f"OpenVPN profile for {cn}"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="chat_id"\r\n\r\n'
        f"{chat_id}\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="caption"\r\n\r\n'
        f"{caption}\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="document"; filename="{cn}.ovpn"\r\n'
        f"Content-Type: application/octet-stream\r\n\r\n"
    ).encode("utf-8") + ovpn_path.read_bytes() + f"\r\n--{boundary}--\r\n".encode(
        "utf-8"
    )

    url = f"https://api.telegram.org/bot{token}/sendDocument"
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise NotifyError(f"Telegram failed: {exc}") from exc
    if not payload.get("ok"):
        raise NotifyError(f"Telegram API error: {payload}")
