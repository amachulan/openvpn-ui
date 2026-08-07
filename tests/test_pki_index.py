from pathlib import Path

import pytest

from vpnctl.pki import PkiError, find_existing_ovpn, parse_index_txt, validate_cn


INDEX = """\
V\t271205120000Z\t\t01\tunknown\t/CN=alice
R\t271205120000Z\t260806120000Z\t02\tunknown\t/CN=bob
V\t271205120000Z\t\t03\tunknown\t/CN=carol/emailAddress=carol@example.com
"""


def test_parse_index_txt():
    certs = {c.cn: c for c in parse_index_txt(INDEX)}
    assert certs["alice"].status == "valid"
    assert certs["alice"].serial == "01"
    assert certs["bob"].status == "revoked"
    assert certs["carol"].status == "valid"


def test_validate_cn():
    assert validate_cn("alice-1") == "alice-1"
    with pytest.raises(PkiError):
        validate_cn("bad name")


def test_find_existing_ovpn(tmp_path: Path):
    out = tmp_path / "clients"
    out.mkdir()
    assert find_existing_ovpn("alice", out) is None
    profile = out / "alice.ovpn"
    profile.write_text("client\n", encoding="utf-8")
    assert find_existing_ovpn("alice", out) == profile
