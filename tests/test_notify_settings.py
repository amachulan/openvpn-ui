from pathlib import Path

from openvpn_ui.config import (
    load_config,
    normalize_mail_settings,
    normalize_telegram_settings,
    persist_notify_settings,
    public_notify_settings,
)


def test_public_notify_settings_redacts_secrets():
    cfg = {
        "mail": {
            "enabled": True,
            "smtp_host": "smtp.example.com",
            "smtp_port": 587,
            "smtp_user": "u",
            "smtp_password": "secret",
            "use_tls": True,
            "from_addr": "vpn@example.com",
            "subject": "Profile",
        },
        "telegram": {
            "enabled": True,
            "bot_token": "123:ABC",
            "chat_id": "42",
        },
    }
    pub = public_notify_settings(cfg)
    assert "smtp_password" not in pub["mail"]
    assert pub["mail"]["smtp_password_set"] is True
    assert "bot_token" not in pub["telegram"]
    assert pub["telegram"]["bot_token_set"] is True
    assert pub["telegram"]["chat_id"] == "42"


def test_persist_notify_keeps_password_when_blank(tmp_path: Path):
    path = tmp_path / "config.yaml"
    path.write_text(
        "api:\n  token: test\nmail:\n  enabled: false\n  smtp_password: keep-me\n"
        "telegram:\n  enabled: false\n  bot_token: tok-1\n",
        encoding="utf-8",
    )
    cfg = load_config(path)
    mail = normalize_mail_settings(
        {
            "enabled": True,
            "smtp_host": "smtp.example.com",
            "smtp_port": 587,
            "smtp_user": "u",
            "smtp_password": "",
            "use_tls": True,
            "from_addr": "vpn@example.com",
            "subject": "Hi",
        },
        cfg.get("mail") or {},
    )
    tg = normalize_telegram_settings(
        {"enabled": True, "bot_token": "", "chat_id": "99"},
        cfg.get("telegram") or {},
    )
    persist_notify_settings(cfg, mail=mail, telegram=tg)

    reloaded = load_config(path)
    assert reloaded["mail"]["enabled"] is True
    assert reloaded["mail"]["smtp_password"] == "keep-me"
    assert reloaded["mail"]["smtp_host"] == "smtp.example.com"
    assert reloaded["telegram"]["bot_token"] == "tok-1"
    assert reloaded["telegram"]["chat_id"] == "99"
    assert reloaded["api"]["token"] == "test"
