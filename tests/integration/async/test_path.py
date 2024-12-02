import pytest
from librouteros.query import Key


@pytest.mark.asyncio
async def test_add_then_remove(routeros_api_async):
    ips = routeros_api_async.path("ip", "address")
    new_id = await ips.add(interface="ether1", address="192.168.1.1/24")
    await ips.remove(new_id)
    _id = Key(".id")
    assert tuple() == tuple([r async for r in ips.select(_id).where(_id == new_id)])


@pytest.mark.asyncio
async def test_add_then_update(routeros_api_async):
    ips = routeros_api_async.path("ip", "address")
    new_id = await ips.add(interface="ether1", address="192.168.1.1/24")
    await ips.update(**{".id": new_id, "address": "172.16.1.1/24"})
    address = Key("address")
    assert [r async for r in ips.select(address).where(Key(".id") == new_id)][0]["address"] == "172.16.1.1/24"
