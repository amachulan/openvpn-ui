from vpnctl.status import parse_openvpn_status


LEGACY = """\
OpenVPN CLIENT LIST
Updated,Thu Aug  6 12:00:00 2026
Common Name,Real Address,Bytes Received,Bytes Sent,Connected Since
alice,1.2.3.4:1194,100,200,Thu Aug  6 11:00:00 2026
ROUTING TABLE
Virtual Address,Common Name,Real Address,Last Ref
10.8.0.2,alice,1.2.3.4:1194,Thu Aug  6 11:59:00 2026
GLOBAL STATS
END
"""

STATUS3 = """\
TITLE\tOpenVPN 2.6
TIME\t2026-08-06 12:00:00
HEADER\tCLIENT_LIST\tCommon Name\tReal Address\tVirtual Address\tBytes Received\tBytes Sent\tConnected Since\tConnected Since (time_t)\tUsername\tClient ID\tPeer ID
CLIENT_LIST\tbob\t5.6.7.8:443\t10.8.0.3\t10\t20\t2026-08-06 11:00:00\t0\tbob\t7\t1
HEADER\tROUTING_TABLE\tVirtual Address\tCommon Name\tReal Address\tLast Ref
ROUTING_LIST\t10.8.0.3\tbob\t5.6.7.8:443\t2026-08-06 11:59:00
GLOBAL_STATS\tMax bcast/mcast queue length\t0
END
"""


def test_parse_legacy_status():
    clients = parse_openvpn_status(LEGACY)
    assert len(clients) == 1
    assert clients[0].cn == "alice"
    assert clients[0].real_address.startswith("1.2.3.4")
    assert clients[0].virtual_address == "10.8.0.2"
    assert clients[0].bytes_received == 100
    assert clients[0].bytes_sent == 200


def test_parse_status_version3():
    clients = parse_openvpn_status(STATUS3)
    assert len(clients) == 1
    assert clients[0].cn == "bob"
    assert clients[0].virtual_address == "10.8.0.3"
    assert clients[0].client_id == "7"
