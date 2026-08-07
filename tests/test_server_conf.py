from pathlib import Path

from openvpn_ui.server_conf import (
    apply_client_endpoint_overrides,
    apply_settings_patch,
    backup_file,
    clone_instance_conf,
    list_backups,
    parse_server_conf,
    restore_backup,
    sync_client_template,
    validate_settings_patch,
    write_server_conf,
)

SAMPLE = """\
port 1194
proto udp
dev tun
server 10.8.0.0 255.255.255.0
push "dhcp-option DNS 1.1.1.1"
push "dhcp-option DNS 1.0.0.1"
push "route 192.168.1.0 255.255.255.0"
push "redirect-gateway def1 bypass-dhcp"
push "block-ipv6"
duplicate-cn
client-to-client
cipher AES-128-GCM
auth SHA256
tls-version-min 1.2
tls-crypt-v2 tls-crypt-v2.key
ca ca.crt
cert server_abc.crt
key server_abc.key
"""


def test_parse_server_conf_angristan_like():
    s = parse_server_conf(SAMPLE)
    assert s.port == 1194
    assert s.proto == "udp"
    assert s.duplicate_cn is True
    assert s.client_to_client is True
    assert s.redirect_gateway is True
    assert s.dns == ["1.1.1.1", "1.0.0.1"]
    assert s.local_networks == ["192.168.1.0/24"]
    assert s.cipher == "AES-128-GCM"
    assert s.tls_mode == "tls-crypt-v2"


def test_apply_settings_patch_round_trip():
    patch = validate_settings_patch(
        {
            "port": 443,
            "proto": "tcp",
            "duplicate_cn": False,
            "client_to_client": True,
            "redirect_gateway": False,
            "dns": ["9.9.9.9"],
            "local_networks": ["10.0.0.0/8"],
            "cipher": "AES-256-GCM",
            "auth": "SHA512",
            "tls_version_min": "1.3",
        }
    )
    text = apply_settings_patch(SAMPLE, patch)
    s = parse_server_conf(text)
    assert s.port == 443
    assert s.proto == "tcp"
    assert s.duplicate_cn is False
    assert s.client_to_client is True
    assert s.redirect_gateway is False
    assert s.dns == ["9.9.9.9"]
    assert s.local_networks == ["10.0.0.0/8"]
    assert s.cipher == "AES-256-GCM"
    assert s.auth == "SHA512"
    assert s.tls_version_min == "1.3"
    assert "tls-crypt-v2" in text
    assert "ca ca.crt" in text


def test_backup_and_restore(tmp_path: Path):
    conf = tmp_path / "server.conf"
    conf.write_text(SAMPLE, encoding="utf-8")
    backup_dir = tmp_path / "backups"
    bak = backup_file(conf, backup_dir, prefix="server.conf")
    assert bak.is_file()
    conf.write_text("port 1\n", encoding="utf-8")
    rows = list_backups(backup_dir, prefix="server.conf")
    assert rows
    restore_backup(backup_dir, bak.name, conf)
    assert "port 1194" in conf.read_text(encoding="utf-8")


def test_write_server_conf_creates_backup(tmp_path: Path):
    conf = tmp_path / "server.conf"
    conf.write_text(SAMPLE, encoding="utf-8")
    backup_dir = tmp_path / "backups"
    bak = write_server_conf(conf, "port 8443\nproto tcp\n", backup_dir)
    assert bak.is_file()
    assert conf.read_text(encoding="utf-8").startswith("port 8443")


def test_sync_client_template(tmp_path: Path):
    tpl = tmp_path / "client-template.txt"
    tpl.write_text("client\nproto udp\nremote vpn.example.com 1194\ndev tun\n", encoding="utf-8")
    assert sync_client_template(tpl, port=443, proto="tcp") is True
    text = tpl.read_text(encoding="utf-8")
    assert "proto tcp" in text
    assert "remote vpn.example.com 443" in text
    assert sync_client_template(tpl, port=443, proto="tcp") is False


def test_clone_instance_conf_tcp():
    sample = SAMPLE + "status /var/log/openvpn/status.log\n"
    sample += "management /var/run/openvpn-server/server.sock unix\n"
    sample += "ifconfig-pool-persist ipp.txt\n"
    text = clone_instance_conf(sample, instance_id="tcp", proto="tcp", port=443)
    s = parse_server_conf(text)
    assert s.port == 443
    assert s.proto == "tcp"
    assert "ca ca.crt" in text
    assert "server 10.8.0.0" in text
    assert "status /var/log/openvpn/status-tcp.log" in text
    assert "management /var/run/openvpn-server/server-tcp.sock unix" in text
    assert "ifconfig-pool-persist ipp-tcp.txt" in text


def test_apply_client_endpoint_overrides():
    text = "client\nproto udp\nremote vpn.example.com 1194\ndev tun\n"
    out = apply_client_endpoint_overrides(text, proto="tcp", port=443)
    assert "proto tcp" in out
    assert "remote vpn.example.com 443" in out
