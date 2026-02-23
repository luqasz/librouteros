# -*- coding: UTF-8 -*-

import asyncio
from collections.abc import Awaitable, Callable
from socket import create_connection, socket
from ssl import SSLContext
from typing import TypedDict

from librouteros.api import Api, AsyncApi
from librouteros.connections import AsyncSocketTransport, SocketTransport
from librouteros.exceptions import ConnectionClosed, FatalError
from librouteros.login import (
    async_plain,
    async_token,  # noqa F401
    plain,
    token,  # noqa F401
)
from librouteros.protocol import ApiProtocol, AsyncApiProtocol


class ConnectKwargs(TypedDict, total=False):
    timeout: int
    port: int
    saddr: str
    subclass: type[Api]
    encoding: str
    ssl_wrapper: Callable[[socket], socket] | None
    login_method: Callable[[Api, str, str], None]

class AsyncConnectKwargs(TypedDict, total=False):
    timeout: int
    port: int
    saddr: str
    subclass: type[AsyncApi]
    encoding: str
    ssl_wrapper: SSLContext | None
    login_method: Callable[[AsyncApi, str, str], Awaitable[None]]

DEFAULTS: ConnectKwargs = {
    "timeout": 10,
    "port": 8728,
    "saddr": "0.0.0.0",  # noqa S104
    "subclass": Api,
    "encoding": "ASCII",
    "ssl_wrapper": None,
    "login_method": plain,
}

ASYNC_DEFAULTS: AsyncConnectKwargs = {
    "timeout": 10,
    "port": 8728,
    "saddr": "0.0.0.0",  # noqa S104
    "subclass": AsyncApi,
    "encoding": "ASCII",
    "ssl_wrapper": None,
    "login_method": async_plain,
}


def connect(
    host: str,
    username: str,
    password: str,
    *,
    timeout: float = DEFAULTS["timeout"],
    port: int = DEFAULTS["port"],
    saddr: str = DEFAULTS["saddr"],
    subclass: type[Api] = DEFAULTS["subclass"],
    encoding: str = DEFAULTS["encoding"],
    ssl_wrapper: Callable[[socket], socket] | None = DEFAULTS["ssl_wrapper"],
    login_method: Callable[[Api, str, str], None] = DEFAULTS["login_method"],
) -> Api:
    """
    Connect and login to routeros device.
    Upon success return an Api class.

    :param host: Hostname to connect to. May be ipv4,ipv6,FQDN.
    :param username: Username to login with.
    :param password: Password to login with. Only ASCII characters allowed.
    :param timeout: Socket timeout. Defaults to 10.
    :param port: Destination port to be used. Defaults to 8728.
    :param saddr: Source address to bind to.
    :param subclass: Subclass of Api class. Defaults to Api class from library.
    :param ssl_wrapper: Callable (e.g. ssl.SSLContext.wrap_socket()) to wrap socket with.
    :param login_method: Callable with login method.
    """
    transport: SocketTransport = create_transport(host, port, ssl_wrapper, saddr, timeout)
    protocol: ApiProtocol = ApiProtocol(transport=transport, encoding=encoding)
    api: Api = subclass(protocol=protocol)

    try:
        login_method(api, username, password)
        return api
    except (ConnectionClosed, FatalError):
        transport.close()
        raise


async def async_connect(
    host: str,
    username: str,
    password: str,
    *,
    timeout: float = ASYNC_DEFAULTS["timeout"],  # noqa A002
    port: int = ASYNC_DEFAULTS["port"],
    saddr: str = ASYNC_DEFAULTS["saddr"],
    subclass: type[AsyncApi] = ASYNC_DEFAULTS["subclass"],
    encoding: str = ASYNC_DEFAULTS["encoding"],
    ssl_wrapper: SSLContext | None = ASYNC_DEFAULTS["ssl_wrapper"],
    login_method: Callable[[AsyncApi, str, str], Awaitable[None]] = ASYNC_DEFAULTS["login_method"],
) -> AsyncApi:
    """
    Connect and login to routeros device.
    Upon success return an AsyncApi class.

    :param host: Hostname to connect to. May be ipv4,ipv6,FQDN.
    :param username: Username to login with.
    :param password: Password to login with. Only ASCII characters allowed.
    :param timeout: Socket timeout. Defaults to 10.
    :param port: Destination port to be used. Defaults to 8728.
    :param saddr: Source address to bind to.
    :param subclass: Subclass of AsyncApi class. Defaults to AsyncApi class from library.
    :param ssl_wrapper: ssl.SSLContext instance to wrap socket with.
    :param login_method: Coroutine with login method.
    """
    transport: AsyncSocketTransport = await async_create_transport(
        host, port, ssl_wrapper, saddr, timeout
    )
    protocol: AsyncApiProtocol = AsyncApiProtocol(
        transport=transport, encoding=encoding, timeout=timeout
    )
    api: AsyncApi = subclass(protocol=protocol)

    try:
        await login_method(api, username, password)
        return api
    except (ConnectionClosed, FatalError):
        await transport.close()
        raise


def create_transport(
    host: str,
    port: int,
    ssl_wrapper: Callable[[socket], socket] | None,
    saddr: str,
    timeout: float,
) -> SocketTransport:
    sock: socket = create_connection(
        (host, port),
        timeout=timeout,
        source_address=(saddr, 0),
    )
    if ssl_wrapper:
        sock = ssl_wrapper(sock)
    return SocketTransport(sock=sock)


async def async_create_transport(
    host: str,
    port: int,
    ssl_wrapper: SSLContext | None,
    saddr: str,
    timeout: float,  # noqa A002
) -> AsyncSocketTransport:
    reader, writer = await asyncio.wait_for(
        asyncio.open_connection(
            host=host,
            port=port,
            ssl=ssl_wrapper,
            local_addr=(saddr, 0),
        ),
        timeout=timeout,
    )
    return AsyncSocketTransport(reader=reader, writer=writer)
