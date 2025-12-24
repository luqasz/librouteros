import pytest


def test_proxy_netcat(routeros_api_sync_netcat):
    api = routeros_api_sync_netcat
    identity = api.path("system", "identity")
    idents = []
    for item in identity:
        idents.append(item)
    assert len(idents[0]["name"]) > 0
    api.close()


def test_proxy_ssh(routeros_api_sync_ssh):
    api = routeros_api_sync_ssh
    identity = api.path("system", "identity")
    idents = []
    for item in identity:
        idents.append(item)
    assert len(idents[0]["name"]) > 0
    api.close()


def test_ssl_netcat(routeros_api_ssl_netcat):
    api = routeros_api_ssl_netcat
    identity = api.path("system", "identity")
    idents = []
    for item in identity:
        idents.append(item)
    assert len(idents[0]["name"]) > 0
    api.close()


def test_ssl_ssh(routeros_api_ssl_ssh):
    api = routeros_api_ssl_ssh
    identity = api.path("system", "identity")
    idents = []
    for item in identity:
        idents.append(item)
    assert len(idents[0]["name"]) > 0
    api.close()


@pytest.mark.asyncio
async def test_proxy_netcat_async(routeros_api_async_netcat):
    identity = routeros_api_async_netcat.path("system", "identity")
    idents = []
    async for item in identity:
        idents.append(item)
    assert len(idents[0]["name"]) > 0


@pytest.mark.asyncio
async def test_proxy_ssh_async(routeros_api_async_ssh):
    identity = routeros_api_async_ssh.path("system", "identity")
    idents = []
    async for item in identity:
        idents.append(item)
    assert len(idents[0]["name"]) > 0
