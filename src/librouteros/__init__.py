# -*- coding: UTF-8 -*-

import asyncio
from collections import ChainMap
import os
import re
import shlex
import signal
import socket
from socket import create_connection
import subprocess

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
    'proxy_command': None,
    'ignore_intr': False,
}

ASYNC_DEFAULTS = {
    "timeout": 10,
    "port": 8728,
    "saddr": "0.0.0.0",  # noqa: S104
    "subclass": AsyncApi,
    "encoding": "ASCII",
    "ssl_wrapper": None,
    "login_method": async_plain,
    'proxy_command': None,
    'ignore_intr': False,
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
    :param proxy_command: String used for proxyed connections.  Understands %h and %p similar to openssh proxy_command option.
    :param ignore_intr: Make proxy_command ignore INTR signals
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
    :param proxy_command: String used for proxyed connections.  Understands %h and %p similar to openssh proxy_command option.
    :param ignore_intr: Make proxy_command ignore INTR signals
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


def proxy_connect(hostport:tuple[str,int], proxy_cmd:str, ignore_intr:bool = False) -> socket.socket:
    host,port = hostport
    mapping = {'%h': host, '%p': str(port) }
    cmdline = shlex.split(re.sub(r'%[hp]',
                    lambda m: mapping[m.group(0)], proxy_cmd))
    s1, s2 = socket.socketpair()

    if os.name == 'posix':
        # This is very Linux oriented, and done at a fairly low level
        # Should have less overhead.
        pid = os.fork()
        if pid == 0:
            # Child runs the proxy command
            s2.close()
            fd = s1.fileno()
            os.dup2(fd, 0)
            os.dup2(fd, 1)
            if ignore_intr: signal.signal(signal.SIGINT, signal.SIG_IGN)

            os.execvp(cmdline[0], cmdline)
            exit(-1)  # Abort if we reach here!
    else:
        # This more portable version should work on Windows
        ic(cmdline)
        s1_in = s1.makefile('rb', buffering=0)
        s1_out = s1.makefile('wb', buffering=0)
        proc = subprocess.Popen(
                cmdline,
                stdin=s1_in,
                stdout=s1_out,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if ignore_intr else 0
            )

    # Close our copies of s1; keep s2 for communication
    s1.close()
    return s2

def create_transport(host: str, **kwargs) -> SocketTransport:
    if kwargs['proxy_command'] is None:
        sock = create_connection(
            (host, kwargs["port"]),
            timeout=kwargs["timeout"],
            source_address=(kwargs["saddr"], 0),
        )
    else:
        sock = proxy_connect(
                (host, kwargs["port"]),
                kwargs['proxy_command'],
                kwargs['ignore_intr'],
        )
    if wrapper := kwargs["ssl_wrapper"]:
        sock = wrapper(sock)
    return SocketTransport(sock=sock)


async def async_create_transport(host: str, **kwargs) -> AsyncSocketTransport:
    if kwargs['proxy_command'] is None:
        reader, writer = await asyncio.wait_for(
          asyncio.open_connection(
              host=host,
              port=kwargs["port"],
              ssl=kwargs["ssl_wrapper"],
              local_addr=(kwargs["saddr"], 0),
          ),
          timeout=kwargs["timeout"],
        )
    else:
        sock = proxy_connect(
                (host, kwargs["port"]),
                kwargs['proxy_command'],
                kwargs['ignore_intr'],
        )
        # Wrap the socket in the asyncio loop...
        reader, writer = await asyncio.wait_for(
          asyncio.open_connection(sock = sock),
          timeout=kwargs["timeout"],
        )

    return AsyncSocketTransport(reader=reader, writer=writer)
