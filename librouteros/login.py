from binascii import unhexlify, hexlify
from hashlib import md5


def encode_password(token, password):
    token = token.encode('ascii', 'strict')
    token = unhexlify(token)
    password = password.encode('ascii', 'strict')
    md = md5()
    md.update(b'\x00' + password + token)
    password = hexlify(md.digest())
    return '00' + password.decode('ascii', 'strict')


def token(api, username, password):
    """Login using pre routeros 6.43 authorization method."""
    sentence = api('/login')
    token = tuple(sentence)[0]['ret']
    encoded = encode_password(token, password)
    tuple(api('/login', **{'name': username, 'response': encoded}))


def plain(api, username, password):
    """Login using post routeros 6.43 authorization method."""
    tuple(api('/login', **{'name': username, 'password': password}))
