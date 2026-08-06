from vpnctl.catalog import Catalog


def test_catalog_meta_and_audit(tmp_path):
    cat = Catalog(tmp_path / "catalog.db")
    meta = cat.upsert_client("alice", label="Alice", email="a@example.com")
    assert meta.label == "Alice"
    meta2 = cat.upsert_client("alice", notes="vip")
    assert meta2.label == "Alice"
    assert meta2.notes == "vip"
    cat.add_event("issue", cn="alice", detail="ok")
    events = cat.list_events()
    assert events[0].action == "issue"
    assert events[0].cn == "alice"
