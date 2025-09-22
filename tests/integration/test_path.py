import pytest

from librouteros.query import Key


def test_add_then_remove(routeros_api_sync):
    api = routeros_api_sync
    ips = api.path("ip", "address")
    new_id = ips.add(interface="ether1", address="192.168.1.1/24")
    ips.remove(new_id)
    _id = Key(".id")
    assert () == tuple(ips.select(_id).where(_id == new_id))


@pytest.mark.asyncio
async def test_add_then_remove_async(routeros_api_async):
    ips = routeros_api_async.path("ip", "address")
    new_id = await ips.add(interface="ether1", address="192.168.1.1/24")
    await ips.remove(new_id)
    _id = Key(".id")
    assert () == tuple([r async for r in ips.select(_id).where(_id == new_id)])


def test_add_then_update(routeros_api_sync):
    api = routeros_api_sync
    ips = api.path("ip", "address")
    new_id = ips.add(interface="ether1", address="192.168.1.1/24")
    ips.update(**{".id": new_id, "address": "172.16.1.1/24"})
    address = Key("address")
    assert next(ips.select(address).where(Key(".id") == new_id))["address"] == "172.16.1.1/24"


@pytest.mark.asyncio
async def test_add_then_update_async(routeros_api_async):
    ips = routeros_api_async.path("ip", "address")
    new_id = await ips.add(interface="ether1", address="192.168.1.1/24")
    await ips.update(**{".id": new_id, "address": "172.16.1.1/24"})
    address = Key("address")
    assert next(r async for r in ips.select(address).where(Key(".id") == new_id))["address"] == "172.16.1.1/24"
