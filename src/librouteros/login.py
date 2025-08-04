# -*- coding: UTF-8 -*-

import typing
from binascii import hexlify, unhexlify
from hashlib import md5


def encode_password(token: str, password: str) -> str:
    token_bytes = token.encode("ascii", "strict")
    token_bytes = unhexlify(token)
    password_bytes = password.encode("ascii", "strict")
    hasher = md5(usedforsecurity=False)
    hasher.update(b"\x00" + password_bytes + token_bytes)
    password_bytes = hexlify(hasher.digest())
    return "00" + password_bytes.decode("ascii", "strict")


def token(api: typing.Any, username: str, password: str) -> None:
    """Login using pre routeros 6.43 authorization method."""
    sentence = api("/login")
    tok = next(iter(sentence))["ret"]
    encoded = encode_password(tok, password)
    tuple(api("/login", **{"name": username, "response": encoded}))


def plain(api: typing.Any, username: str, password: str) -> None:
    """Login using post routeros 6.43 authorization method."""
    tuple(api("/login", **{"name": username, "password": password}))


async def async_plain(api, username, password):
    [response async for response in api("/login", **{"name": username, "password": password})]


async def async_token(api: typing.Any, username: str, password: str) -> None:
    """Login using pre routeros 6.43 authorization method."""
    sentence = [response async for response in api("/login")]
    tok = sentence[0]["ret"]
    encoded = encode_password(tok, password)
    [response async for response in api("/login", **{"name": username, "response": encoded})]
