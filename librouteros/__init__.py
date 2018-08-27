# -*- coding: UTF-8 -*-

from socket import create_connection, error as SOCKET_ERROR, timeout as SOCKET_TIMEOUT
from binascii import unhexlify, hexlify
from hashlib import md5
try:
    from collections import ChainMap
except ImportError:
    from chainmap import ChainMap

from librouteros.exceptions import TrapError, FatalError, ConnectionError, MultiTrapError
from librouteros.connections import ApiProtocol, SocketTransport
from librouteros.api import Api


defaults = {
            'timeout': 10,
            'port': 8728,
            'saddr': '',
            'subclass': Api,
            'encoding': 'ASCII',
            'ssl_wrapper': lambda sock: sock,
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
    """
    arguments = ChainMap(kwargs, defaults)
    transport = create_transport(host, **arguments)
    protocol = ApiProtocol(transport=transport, encoding=arguments['encoding'])
    api = arguments['subclass'](protocol=protocol)

    try:
        # First send dummy credentials to know if we get a =ret= back.
        # This way we know if it is a pre 6.43 auth method or not.
        sentence = api('/login', **{'name': 'dummy_user', 'password': 'dummy_password'})
        token = sentence[0]['ret']
    except (TrapError, MultiTrapError):
        # Login failed so use 6.43 auth method.
        api('/login', **{'name': username, 'password': password})
    except (ConnectionError, FatalError):
        transport.close()
        raise
    else:
        # We got =ret= so use pre 6.43 auth method.
        api('/login', **{'name': username, 'response': encode_password(token, password)})

    return api


def create_transport(host, **kwargs):
    try:
        sock = create_connection((host, kwargs['port']), kwargs['timeout'], (kwargs['saddr'], 0))
        sock = kwargs['ssl_wrapper'](sock)
        return SocketTransport(sock)
    except (SOCKET_ERROR, SOCKET_TIMEOUT) as error:
        raise ConnectionError(error)
    return SocketTransport(sock=sock)


def encode_password(token, password):

    token = token.encode('ascii', 'strict')
    token = unhexlify(token)
    password = password.encode('ascii', 'strict')
    md = md5()
    md.update(b'\x00' + password + token)
    password = hexlify(md.digest())
    return '00' + password.decode('ascii', 'strict')
