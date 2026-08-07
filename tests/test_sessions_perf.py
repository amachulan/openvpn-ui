from pathlib import Path

from vpnctl.service import VpnctlService


def test_list_sessions_uses_empty_status_file_without_management(tmp_path: Path, monkeypatch):
    status = tmp_path / "status.log"
    status.write_text(
        "TITLE\tOpenVPN\nTIME\tnow\nHEADER\tCLIENT_LIST\tCommon Name\nEND\n",
        encoding="utf-8",
    )
    cfg = {
        "paths": {
            "status_log": str(status),
            "catalog_db": str(tmp_path / "catalog.db"),
            "easy_rsa_dir": str(tmp_path / "easy-rsa"),
            "server_conf": str(tmp_path / "server.conf"),
            "openvpn_server_dir": str(tmp_path),
            "client_template": str(tmp_path / "tpl"),
            "crl_publish": str(tmp_path / "crl.pem"),
            "client_output_dir": str(tmp_path / "clients"),
        },
        "api": {"host": "127.0.0.1", "port": 8080, "token": "x"},
        "openvpn_management": {"timeout_seconds": 15},
    }

    def boom(_endpoint):
        raise AssertionError("management should not be called when status file exists")

    monkeypatch.setattr("vpnctl.service.OpenVpnManagementClient", boom)
    assert VpnctlService(cfg).list_sessions() == []
