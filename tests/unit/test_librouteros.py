# -*- coding: UTF-8 -*-
import socket
from unittest.mock import (
    Mock,
    patch,
)

import pytest

from librouteros import (
    DEFAULTS,
    ASYNC_DEFAULTS,
    Api,
    AsyncApi,
    async_connect,
    connect,
    create_transport,
    async_create_transport,
)
from librouteros.exceptions import TrapError
from librouteros.login import (
    encode_password,
    plain,
    async_plain,
)


@pytest.mark.parametrize(
    ("key", "value"),
    (
        ("timeout", 10),
        ("port", 8728),
        ("saddr", ""),
        ("subclass", Api),
        ("encoding", "ASCII"),
        ("login_method", plain),
        ("ssl_wrapper", None),
    ),
)
def test_defaults(key, value):
    assert DEFAULTS[key] == value


@pytest.mark.parametrize(
    ("key", "value"),
    (
        ("timeout", 10),
        ("port", 8728),
        ("saddr", ""),
        ("subclass", AsyncApi),
        ("encoding", "ASCII"),
        ("login_method", async_plain),
        ("ssl_wrapper", None),
    ),
)
def test_async_defaults(key, value):
    assert ASYNC_DEFAULTS[key] == value


def test_default_keys():
    assert set(DEFAULTS.keys()) == {
        "timeout",
        "port",
        "saddr",
        "subclass",
        "encoding",
        "login_method",
        "ssl_wrapper",
    }


def test_async_default_keys():
    assert set(ASYNC_DEFAULTS.keys()) == {
        "timeout",
        "port",
        "saddr",
        "subclass",
        "encoding",
        "login_method",
        "ssl_wrapper",
    }


def test_password_encoding():
    result = encode_password("259e0bc05acd6f46926dc2f809ed1bba", "test")
    assert result == "00c7fd865183a43a772dde231f6d0bff13"


def test_non_ascii_password_encoding():
    """Only ascii characters are allowed in password."""
    with pytest.raises(UnicodeEncodeError):
        encode_password(token="259e0bc05acd6f46926dc2f809ed1bba", password="łą")  # noqa S106


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
    kwargs = {
        "host": "127.0.0.1",
        "port": 22,
        "timeout": 2,
        "saddr": "",
    }
    transport.side_effect = exc
    with pytest.raises(exc):
        create_transport(**kwargs)


@pytest.mark.asyncio
@pytest.mark.parametrize("exc", (socket.error, socket.timeout))
@patch("librouteros.create_connection")
@patch("librouteros.SocketTransport")
async def test_async_create_connection_does_not_wrap_socket_exceptions(create_connection, transport, exc):
    kwargs = {
        "host": "127.0.0.1",
        "port": 22,
        "timeout": 2,
        "saddr": "",
    }
    transport.side_effect = exc
    with pytest.raises(exc):
        await create_transport(**kwargs)


@patch("librouteros.create_connection")
def test_crate_transport_calls_ssl_wrapper(connection_mock):
    params = DEFAULTS.copy()
    params["ssl_wrapper"] = Mock()
    create_transport(host="127.0.0.1", **params)
    params["ssl_wrapper"].assert_called_once_with(connection_mock.return_value)


@pytest.mark.asyncio
@patch("librouteros.asyncio.open_connection")
async def test_async_crate_transport_passes_ssl_wrapper(connection_mock):
    params = ASYNC_DEFAULTS.copy()
    params["ssl_wrapper"] = Mock()
    connection_mock.return_value = (Mock(), Mock())
    await async_create_transport(host="127.0.0.1", **params)
    assert connection_mock.call_args.kwargs["ssl"] == params["ssl_wrapper"]
