import ipaddress
from pathlib import Path

from openvpn_ui.access import (
    client_ip_allowed,
    is_loopback_bind,
    parse_vpn_pool_cidrs,
    resolve_allow_networks,
)


def test_is_loopback_bind():
    assert is_loopback_bind("127.0.0.1")
    assert is_loopback_bind("localhost")
    assert not is_loopback_bind("0.0.0.0")
    assert not is_loopback_bind("10.0.0.5")


def test_parse_vpn_pool_cidrs(tmp_path: Path):
    conf = tmp_path / "server.conf"
    conf.write_text(
        "port 1194\n"
        "server 10.8.0.0 255.255.255.0\n"
        "server-ipv6 fd42:42:42:42::/112\n",
        encoding="utf-8",
    )
    cidrs = parse_vpn_pool_cidrs(conf)
    assert "10.8.0.0/24" in cidrs
    assert any(c.startswith("fd42:42:42:42::") for c in cidrs)


def test_client_ip_allowed():
    nets = [ipaddress.ip_network("10.8.0.0/24")]
    assert client_ip_allowed("10.8.0.14", nets)
    assert not client_ip_allowed("1.2.3.4", nets)
    assert client_ip_allowed("1.2.3.4", [])


def test_resolve_allow_from_vpn(tmp_path: Path):
    conf = tmp_path / "server.conf"
    conf.write_text("server 10.8.0.0 255.255.255.0\n", encoding="utf-8")
    cfg = {
        "paths": {"server_conf": str(conf)},
        "api": {
            "allow_from": ["127.0.0.1/32"],
            "allow_from_vpn": True,
        },
    }
    nets = resolve_allow_networks(cfg)
    assert any(str(n) == "127.0.0.1/32" for n in nets)
    assert any(str(n) == "10.8.0.0/24" for n in nets)
