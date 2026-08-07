from pathlib import Path

import pytest

from openvpn_ui.pki import (
    PkiError,
    find_existing_ovpn,
    is_server_cn,
    parse_index_expiry,
    parse_index_txt,
    server_certificate_cns,
    validate_cn,
)


INDEX = """\
V\t271205120000Z\t\t01\tunknown\t/CN=alice
R\t271205120000Z\t260806120000Z\t02\tunknown\t/CN=bob
V\t271205120000Z\t\t03\tunknown\t/CN=carol/emailAddress=carol@example.com
V\t360804120000Z\t\t04\tunknown\t/CN=server_Dm9Tng6TdB86pURf
"""


def test_parse_index_txt():
    certs = {c.cn: c for c in parse_index_txt(INDEX)}
    assert certs["alice"].status == "valid"
    assert certs["alice"].serial == "01"
    assert certs["alice"].expires_at == "2027-12-05"
    assert certs["bob"].status == "revoked"
    assert certs["carol"].status == "valid"
    assert "server_Dm9Tng6TdB86pURf" in certs


def test_parse_index_expiry():
    day, days = parse_index_expiry("360804120000Z")
    assert day == "2036-08-04"
    assert days is not None


def test_validate_cn():
    assert validate_cn("alice-1") == "alice-1"
    with pytest.raises(PkiError):
        validate_cn("bad name")


def test_is_server_cn():
    assert is_server_cn("server_Dm9Tng6TdB86pURf")
    assert is_server_cn("server")
    assert not is_server_cn("machulan")
    assert is_server_cn("custom", {"custom"})


def test_server_certificate_cns(tmp_path: Path):
    conf = tmp_path / "server.conf"
    conf.write_text("cert server_Dm9Tng6TdB86pURf.crt\nport 1194\n", encoding="utf-8")
    assert server_certificate_cns(conf) == {"server_Dm9Tng6TdB86pURf"}


def test_find_existing_ovpn(tmp_path: Path):
    out = tmp_path / "clients"
    out.mkdir()
    assert find_existing_ovpn("alice", out) is None
    profile = out / "alice.ovpn"
    profile.write_text("client\n", encoding="utf-8")
    assert find_existing_ovpn("alice", out) == profile
