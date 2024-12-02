import pytest


@pytest.mark.asyncio
async def test_generator_ditch(routeros_api_async):
    """
    Assert that after ditching generator, new one will yield actual results.
    """
    routeros_api_async(
        "/ip/address/add",
        address="1.1.1.1/32",
        interface="ether1",
    )
    ips = routeros_api_async.path("ip", "address")
    async for ip in ips:
        break

    interfaces = [r async for r in routeros_api_async.path("interface")]
    assert len(interfaces) == 1
    assert "mtu" in interfaces[0].keys()
    assert "mac-address" in interfaces[0].keys()
