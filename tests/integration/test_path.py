from librouteros.query import Key


def test_add_then_remove(routeros_api):
    ips = routeros_api.path("ip", "address")
    new_id = ips.add(interface="ether1", address="192.168.1.1/24")
    ips.remove(new_id)
    _id = Key(".id")
    assert tuple() == tuple(ips.select(_id).where(_id == new_id))


def test_add_then_update(routeros_api):
    ips = routeros_api.path("ip", "address")
    new_id = ips.add(interface="ether1", address="192.168.1.1/24")
    ips.update(**{".id": new_id, "address": "172.16.1.1/24"})
    address = Key("address")
    assert tuple(ips.select(address).where(Key(".id") == new_id))[0]["address"] == "172.16.1.1/24"
