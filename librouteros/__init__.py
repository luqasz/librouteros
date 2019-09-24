# -*- coding: UTF-8 -*-

from socket import create_connection, error as SOCKET_ERROR, timeout as SOCKET_TIMEOUT
try:
    from collections import ChainMap
except ImportError:
    from chainmap import ChainMap

from librouteros.exceptions import TrapError, FatalError, ConnectionError, MultiTrapError
from librouteros.connections import ApiProtocol, SocketTransport
from librouteros.login import login_plain, login_token
from librouteros.api import Api


defaults = {
            'timeout': 10,
            'port': 8728,
            'saddr': '',
            'subclass': Api,
            'encoding': 'ASCII',
            'ssl_wrapper': lambda sock: sock,
            'login_methods': (login_token, login_plain),
            }


def connect(host, username, password, **kwargs):
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
    :param login_methods: Tuple with callables to login methods to try in order.
    """
    arguments = ChainMap(kwargs, defaults)
    transport = create_transport(host, **arguments)
    protocol = ApiProtocol(transport=transport, encoding=arguments['encoding'])
    api = arguments['subclass'](protocol=protocol)

    for method in arguments['login_methods']:
        try:
            method(api=api, username=username, password=password)
            return api
        except (TrapError, MultiTrapError) as error:
            trap = error
        except (ConnectionError, FatalError):
            transport.close()
            raise

    raise trap


def create_transport(host, **kwargs):
    try:
        sock = create_connection((host, kwargs['port']), kwargs['timeout'], (kwargs['saddr'], 0))
        sock = kwargs['ssl_wrapper'](sock)
        return SocketTransport(sock)
    except (SOCKET_ERROR, SOCKET_TIMEOUT) as error:
        raise ConnectionError(error)
    return SocketTransport(sock=sock)
