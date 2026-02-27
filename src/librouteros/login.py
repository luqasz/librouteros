# -*- coding: UTF-8 -*-

from binascii import hexlify, unhexlify
from hashlib import md5

from librouteros.api import Api, AsyncApi
from librouteros.types import ReplyDict, ResponseIter


def encode_password(token: str, password: str) -> str:
    token_bytes: bytes = token.encode("ascii", "strict")
    token_bytes = unhexlify(token)
    password_bytes: bytes = password.encode("ascii", "strict")
    hasher = md5(usedforsecurity=False)
    hasher.update(b"\x00" + password_bytes + token_bytes)
    password_bytes = hexlify(hasher.digest())
    return "00" + password_bytes.decode("ascii", "strict")


def token(api: Api, username: str, password: str) -> None:
    """Login using pre routeros 6.43 authorization method."""
    sentence: ResponseIter = api("/login")
    tok: str = str(next(iter(sentence))["ret"])
    encoded: str = encode_password(tok, password)
    tuple(api("/login", **{"name": username, "response": encoded}))


def plain(api: Api, username: str, password: str) -> None:
    """Login using post routeros 6.43 authorization method."""
    tuple(api("/login", **{"name": username, "password": password}))


async def async_plain(api: AsyncApi, username: str, password: str) -> None:
    [response async for response in api("/login", **{"name": username, "password": password})]


async def async_token(api: AsyncApi, username: str, password: str) -> None:
    """Login using pre routeros 6.43 authorization method."""
    sentence: list[ReplyDict] = [response async for response in api("/login")]
    tok: str = str(sentence[0]["ret"])
    encoded: str = encode_password(tok, password)
    [response async for response in api("/login", **{"name": username, "response": encoded})]
