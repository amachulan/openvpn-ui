from pathlib import Path
from unittest.mock import patch

from openvpn_ui.instances import default_instances, resolve_instances
from openvpn_ui.service import OpenVpnUiService


SAMPLE = """\
port 1194
proto udp
dev tun
server 10.8.0.0 255.255.255.0
ca ca.crt
cert server.crt
key server.key
status /var/log/openvpn/status.log
management /var/run/openvpn-server/server.sock unix
ifconfig-pool-persist ipp.txt
"""


def _cfg(tmp_path: Path, conf: Path) -> dict:
    return {
        "paths": {
            "openvpn_server_dir": str(tmp_path),
            "easy_rsa_dir": str(tmp_path / "easy-rsa"),
            "server_conf": str(conf),
            "client_template": str(tmp_path / "client-template.txt"),
            "status_log": str(tmp_path / "status.log"),
            "crl_publish": str(tmp_path / "crl.pem"),
            "client_output_dir": str(tmp_path / "clients"),
            "catalog_db": str(tmp_path / "catalog.db"),
            "server_conf_backup_dir": str(tmp_path / "backups"),
        },
        "openvpn": {"service": "", "instances": {}},
        "_config_path": str(tmp_path / "config.yaml"),
    }


def test_default_instances_udp_primary(tmp_path: Path):
    conf = tmp_path / "server.conf"
    conf.write_text(SAMPLE, encoding="utf-8")
    cfg = _cfg(tmp_path, conf)
    inst = default_instances(cfg)
    assert inst["udp"]["primary"] is True
    assert inst["udp"]["enabled"] is True
    assert inst["tcp"]["primary"] is False
    assert inst["tcp"]["enabled"] is False
    assert inst["tcp"]["conf"].endswith("server-tcp.conf")
    assert inst["tcp"]["service"] == "openvpn-server@server-tcp"


def test_resolve_enables_secondary_when_conf_exists(tmp_path: Path):
    conf = tmp_path / "server.conf"
    conf.write_text(SAMPLE, encoding="utf-8")
    tcp = tmp_path / "server-tcp.conf"
    tcp.write_text("port 443\nproto tcp\n", encoding="utf-8")
    cfg = _cfg(tmp_path, conf)
    inst = resolve_instances(cfg)
    assert inst["tcp"]["enabled"] is True


def test_enable_instance_clones_and_systemctl(tmp_path: Path):
    conf = tmp_path / "server.conf"
    conf.write_text(SAMPLE, encoding="utf-8")
    cfg = _cfg(tmp_path, conf)
    (tmp_path / "config.yaml").write_text("openvpn: {}\n", encoding="utf-8")
    svc = OpenVpnUiService(cfg)
    with patch("openvpn_ui.service.openvpn_svc.enable_now") as enable_now:
        enable_now.return_value = {
            "unit": "openvpn-server@server-tcp",
            "ok": True,
        }
        out = svc.enable_instance("tcp")
    dst = tmp_path / "server-tcp.conf"
    assert dst.is_file()
    text = dst.read_text(encoding="utf-8")
    assert "proto tcp" in text
    assert "port 443" in text
    assert "status /var/log/openvpn/status-tcp.log" in text
    assert "ca ca.crt" in text
    enable_now.assert_called_once_with("openvpn-server@server-tcp")
    assert out["instances"]["tcp"]["enabled"] is True
