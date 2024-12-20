# -*- coding: UTF-8 -*-
import socket
import pytest
from unittest.mock import (
    patch,
    Mock,
)
from librouteros import (
    DEFAULTS,
    Api,
    connect,
    async_connect,
    create_transport,
)
from librouteros.exceptions import TrapError
from librouteros.login import (
    encode_password,
    plain,
)


def test_default_ssl_wrapper():
    """Assert that wrapper returns same object as it was called with."""
    assert DEFAULTS["ssl_wrapper"](int) is int


@pytest.mark.parametrize(
    "key, value",
    (
        ("timeout", 10),
        ("port", 8728),
        ("saddr", ""),
        ("subclass", Api),
        ("encoding", "ASCII"),
        ("login_method", plain),
    ),
)
def test_defaults(key, value):
    assert DEFAULTS[key] == value


def test_default_keys():
    assert set(DEFAULTS.keys()) == set(
        (
            "timeout",
            "port",
            "saddr",
            "subclass",
            "encoding",
            "login_method",
            "ssl_wrapper",
        )
    )


def test_password_encoding():
    result = encode_password("259e0bc05acd6f46926dc2f809ed1bba", "test")
    assert result == "00c7fd865183a43a772dde231f6d0bff13"


def test_non_ascii_password_encoding():
    """Only ascii characters are allowed in password."""
    with pytest.raises(UnicodeEncodeError):
        encode_password(token="259e0bc05acd6f46926dc2f809ed1bba", password="łą")


@patch("librouteros.create_transport")
def test_connect_raises_when_failed_login(transport_mock):
    failed = Mock(name="failed", side_effect=TrapError(message="failed to login"))
    with pytest.raises(TrapError):
        connect(host="127.0.0.1", username="admin", password="", login_method=failed)


@pytest.mark.asyncio
@patch("librouteros.async_create_transport")
async def test_async_connect_raises_when_failed_login(transport_mock):
    failed = Mock(name="failed", side_effect=TrapError(message="failed to login"))
    with pytest.raises(TrapError):
        await async_connect(host="127.0.0.1", username="admin", password="", login_method=failed)


@pytest.mark.parametrize("exc", (socket.error, socket.timeout))
@patch("librouteros.create_connection")
@patch("librouteros.SocketTransport")
def test_create_connection_does_not_wrap_socket_exceptions(create_connection, transport, exc):
    kwargs = dict(
        host="127.0.0.1",
        port=22,
        timeout=2,
        saddr="",
    )
    transport.side_effect = exc
    with pytest.raises(exc):
        create_transport(**kwargs)


@pytest.mark.asyncio
@pytest.mark.parametrize("exc", (socket.error, socket.timeout))
@patch("librouteros.create_connection")
@patch("librouteros.SocketTransport")
async def test_async_create_connection_does_not_wrap_socket_exceptions(create_connection, transport, exc):
    kwargs = dict(
        host="127.0.0.1",
        port=22,
        timeout=2,
        saddr="",
    )
    transport.side_effect = exc
    with pytest.raises(exc):
        await create_transport(**kwargs)
