# -*- coding: UTF-8 -*-

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
            'subclass': Api,
            'encoding': 'ASCII',
            }


def login(username, password, sock, **kwargs):
    """
    Login to routeros device.

    Upon success return a Connection class.

    :param username: Username to login with.
    :param password: Password to login with. Only ASCII characters allowed.
    :param sock: Connected socket. May be SSL/TLS or plain TCP.
    :param subclass: Subclass of Api class. Defaults to Api class from library.
    """
    arguments = ChainMap(kwargs, defaults)
    transport = SocketTransport(sock=sock)
    protocol = ApiProtocol(transport=transport, encoding=arguments['encoding'])
    api = arguments['subclass'](protocol=protocol)

    try:
        sentence = api('/login')
        token = sentence[0]['ret']
        encoded = encode_password(token, password)
        api('/login', name=username, response=encoded)
    except (ConnectionError, TrapError, FatalError, MultiTrapError):
        transport.close()
        raise

    return api


def encode_password(token, password):

    token = token.encode('ascii', 'strict')
    token = unhexlify(token)
    password = password.encode('ascii', 'strict')
    md = md5()
    md.update(b'\x00' + password + token)
    password = hexlify(md.digest())
    return '00' + password.decode('ascii', 'strict')
