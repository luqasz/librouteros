import pytest

pytestmark = pytest.mark.xfail


def test_generator_ditch(routeros_api_sync):
    """
    Assert that after ditching generator, new one will yield actual results.
    """
    api = routeros_api_sync
    api(
        "/ip/address/add",
        address="1.1.1.1/32",
        interface="ether1",
    )
    ips = api.path("ip", "address")
    for ip in ips:
        break

    for item in api.path("/interface"):
        assert "mtu" in item.keys()
        assert "mac-address" in item.keys()


@pytest.mark.asyncio
async def test_generator_ditch_async(routeros_api_async):
    """
    Assert that after ditching generator, new one will yield actual results.
    """
    api = routeros_api_async
    api(
        "/ip/address/add",
        address="1.1.1.1/32",
        interface="ether1",
    )
    ips = api.path("ip", "address")
    async for ip in ips:
        break

    async for item in api.path("/interface"):
        assert "mtu" in item.keys()
        assert "mac-address" in item.keys()
