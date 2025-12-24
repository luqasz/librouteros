# -*- coding: UTF-8 -*-

import asyncio
import os
import shlex
import socket
from collections import ChainMap
from socket import create_connection

from librouteros.api import Api, AsyncApi
from librouteros.connections import AsyncSocketTransport, SocketTransport
from librouteros.exceptions import (
    ConnectionClosed,
    FatalError,
)
from librouteros.login import (
    async_plain,
    async_token,  # noqa F401
    plain,
    token,  # noqa F401
)
from librouteros.protocol import ApiProtocol, AsyncApiProtocol

DEFAULTS = {
    "timeout": 10,
    "port": 8728,
    "saddr": "0.0.0.0",  # noqa: S104
    "subclass": Api,
    "encoding": "ASCII",
    "ssl_wrapper": None,
    "login_method": plain,
    "proxy_command": None,
}

ASYNC_DEFAULTS = {
    "timeout": 10,
    "port": 8728,
    "saddr": "0.0.0.0",  # noqa: S104
    "subclass": AsyncApi,
    "encoding": "ASCII",
    "ssl_wrapper": None,
    "login_method": async_plain,
    "proxy_command": None,
}


def connect(host: str, username: str, password: str, **kwargs) -> Api:
    """
    Connect and login to routeros device.
    Upon success return a Api class.

    :param host: Hostname to connecto to. May be ipv4,ipv6,FQDN.
    :param username: Username to login with.
    :param password: Password to login with. Only ASCII characters allowed.
    :param timeout: Socket timeout. Defaults to 10.
    :param port: Destination port to be used. Defaults to 8728.
    :param saddr: Source address to bind to.
    :param subclass: Subclass of Api class. Defaults to Api class from library.
    :param ssl_wrapper: Callable (e.g. ssl.SSLContext instance) to wrap socket with.
    :param login_method: Callable with login method.
    :param proxy_command: Command used for proxyed connections.  Use %h and %p for host and port.
    """
    arguments = ChainMap(kwargs, DEFAULTS)
    transport = create_transport(host, **arguments)
    protocol = ApiProtocol(transport=transport, encoding=arguments["encoding"])
    api: Api = arguments["subclass"](protocol=protocol)

    try:
        arguments["login_method"](api=api, username=username, password=password)
        return api
    except (ConnectionClosed, FatalError):
        transport.close()
        raise


async def async_connect(host: str, username: str, password: str, **kwargs) -> AsyncApi:
    """
    Connect and login to routeros device.
    Upon success return a Api class.

    :param host: Hostname to connecto to. May be ipv4,ipv6,FQDN.
    :param username: Username to login with.
    :param password: Password to login with. Only ASCII characters allowed.
    :param timeout: Socket timeout. Defaults to 10.
    :param port: Destination port to be used. Defaults to 8728.
    :param saddr: Source address to bind to.
    :param subclass: Subclass of Api class. Defaults to Api class from library.
    :param ssl_wrapper: Callable (e.g. ssl.SSLContext instance) to wrap socket with.
    :param login_method: Callable with login method.
    :param proxy_command: Command used for proxyed connections.  Use %h and %p for host and port.
    """
    arguments = ChainMap(kwargs, ASYNC_DEFAULTS)
    transport = await async_create_transport(host, **arguments)
    protocol = AsyncApiProtocol(transport=transport, encoding=arguments["encoding"], timeout=arguments["timeout"])
    api: AsyncApi = arguments["subclass"](protocol=protocol)

    try:
        await arguments["login_method"](api=api, username=username, password=password)
        return api
    except (ConnectionClosed, FatalError):
        await transport.close()
        raise


def proxy_connect(hostport: tuple[str, int], proxy_cmd: str) -> socket.socket:
    host, port = hostport
    proxy_cmd = proxy_cmd.replace("%p", str(port)).replace("%h", host)
    cmdline = shlex.split(proxy_cmd)

    s1, s2 = socket.socketpair()

    if os.name != "posix":
        raise NotImplementedError("Requires a posix environment")

    # This is very Linux oriented, and done at a fairly low level
    # Should have less overhead.
    pid = os.fork()
    if pid == 0:
        # Child runs the proxy command
        s2.close()
        fd = s1.fileno()
        os.dup2(fd, 0)
        os.dup2(fd, 1)

        # We re-fork to lose connection to parent!
        pid = os.fork()
        if pid == 0:
            os.execvp(cmdline[0], cmdline)  # noqa: S606
            exit(-1)  # Abort if we reach here!
        else:
            os._exit(0)  # Exit like this because we do not need any clean-ups!

    # Close our copies of s1; keep s2 for communication
    s1.close()
    os.waitpid(pid, 0)  # Make sure we leave no zombies around...

    return s2


def create_transport(host: str, **kwargs) -> SocketTransport:
    if "proxy_command" not in kwargs or kwargs["proxy_command"] is None:
        sock = create_connection(
            (host, kwargs["port"]),
            timeout=kwargs["timeout"],
            source_address=(kwargs["saddr"], 0),
        )
    else:
        sock = proxy_connect(
            (host, kwargs["port"]),
            kwargs["proxy_command"],
        )
    if wrapper := kwargs["ssl_wrapper"]:
        sock = wrapper(sock)
    return SocketTransport(sock=sock)


async def async_create_transport(host: str, **kwargs) -> AsyncSocketTransport:
    if "proxy_command" not in kwargs or kwargs["proxy_command"] is None:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(
                host=host,
                port=kwargs["port"],
                ssl=kwargs["ssl_wrapper"],
                local_addr=(kwargs["saddr"], 0),
            ),
            timeout=kwargs["timeout"],
        )
        return AsyncSocketTransport(reader=reader, writer=writer)
    else:
        sock = proxy_connect(
            (host, kwargs["port"]),
            kwargs["proxy_command"],
        )
        # Wrap the socket in the asyncio loop...
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(sock=sock),
            timeout=kwargs["timeout"],
        )
        return AsyncSocketTransport(reader=reader, writer=writer)
