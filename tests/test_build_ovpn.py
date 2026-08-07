from pathlib import Path

from openvpn_ui.pki import build_ovpn


def test_build_ovpn_proto_port_override(tmp_path: Path):
    easy = tmp_path / "easy-rsa"
    pki_dir = easy / "pki"
    (pki_dir / "issued").mkdir(parents=True)
    (pki_dir / "private").mkdir(parents=True)
    (pki_dir / "ca.crt").write_text("-----BEGIN CERTIFICATE-----\nCA\n-----END CERTIFICATE-----\n")
    (pki_dir / "issued" / "alice.crt").write_text(
        "-----BEGIN CERTIFICATE-----\nCERT\n-----END CERTIFICATE-----\n"
    )
    (pki_dir / "private" / "alice.key").write_text(
        "-----BEGIN PRIVATE KEY-----\nKEY\n-----END PRIVATE KEY-----\n"
    )
    server_dir = tmp_path / "server"
    server_dir.mkdir()
    server_conf = server_dir / "server.conf"
    server_conf.write_text("port 1194\nproto udp\nca ca.crt\n", encoding="utf-8")
    template = tmp_path / "client-template.txt"
    template.write_text(
        "client\nproto udp\nremote vpn.example.com 1194\ndev tun\nnobind\n",
        encoding="utf-8",
    )
    out_dir = tmp_path / "clients"

    path = build_ovpn(
        easy_rsa_dir=easy,
        server_dir=server_dir,
        server_conf=server_conf,
        client_template=template,
        cn="alice",
        output_dir=out_dir,
        proto="tcp",
        port=443,
        filename_suffix="tcp",
    )
    assert path.name == "alice-tcp.ovpn"
    text = path.read_text(encoding="utf-8")
    assert "proto tcp" in text
    assert "remote vpn.example.com 443" in text
    assert "<ca>" in text
    assert "<cert>" in text
    assert "<key>" in text
