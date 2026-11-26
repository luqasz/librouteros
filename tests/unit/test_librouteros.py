# -*- coding: UTF-8 -*-
import socket
from unittest.mock import (
    AsyncMock,
    Mock,
    call,
    patch,
)

import pytest

from librouteros import (
    ASYNC_DEFAULTS,
    DEFAULTS,
    Api,
    AsyncApi,
    async_connect,
    async_create_transport,
    connect,
    create_transport,
)
from librouteros.exceptions import TrapError
from librouteros.login import (
    async_plain,
    encode_password,
    plain,
)

TRANSPORT_PARAMS = ("timeout", "port", "saddr", "ssl_wrapper")


@pytest.mark.parametrize(
    ("key", "value"),
    (
        ("timeout", 10),
        ("port", 8728),
        ("saddr", None),
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
        ("saddr", None),
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


@patch("librouteros.create_connection")
def test_create_transport_passes_src_addr(conn_mock):
    create_transport(
        host="127.0.0.1",
        port=234,
        saddr="1.1.1.1",
        timeout=20,
    )
    assert conn_mock.call_args == call(
        ("127.0.0.1", 234),
        timeout=20,
        source_address=("1.1.1.1", 0),
    )


@pytest.mark.asyncio
@patch("librouteros.asyncio.open_connection")
async def test_async_create_transport_passes_src_addr(conn_mock):
    conn_mock.return_value = (Mock(), Mock())
    await async_create_transport(
        host="127.0.0.1",
        port=234,
        saddr="1.1.1.1",
        timeout=20,
    )
    assert conn_mock.call_args == call(
        host="127.0.0.1",
        port=234,
        local_addr=("1.1.1.1", 0),
        ssl=None,
    )


@patch("librouteros.create_connection")
def test_crate_transport_calls_ssl_wrapper(connection_mock):
    ssl_wrapper = Mock()
    transport = create_transport(
        host="127.0.0.1",
        port=234,
        saddr="1.1.1.1",
        timeout=20,
        ssl_wrapper=ssl_wrapper,
    )
    ssl_wrapper.assert_called_once_with(connection_mock.return_value)
    assert transport.sock == ssl_wrapper.return_value


@patch("librouteros.create_connection")
def test_crate_transport_does_not_call_ssl_wrapper(connection_mock):
    transport = create_transport(
        host="127.0.0.1",
        port=234,
        saddr="1.1.1.1",
        timeout=20,
        ssl_wrapper=None,
    )
    assert transport.sock == connection_mock.return_value


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


@patch("librouteros.create_transport")
def test_connect_closes_transport_on_failed_login(transport_mock):
    # A failed login must not leak the open socket.
    failed = Mock(name="failed", side_effect=TrapError(message="failed to login"))
    with pytest.raises(TrapError):
        connect(host="127.0.0.1", username="admin", password="", login_method=failed)
    transport_mock.return_value.close.assert_called_once_with()


@patch("librouteros.create_transport")
def test_connect_does_not_close_transport_on_success(transport_mock):
    # A successful login keeps the transport open for the returned Api.
    connect(host="127.0.0.1", username="admin", password="", login_method=Mock(name="ok"))
    transport_mock.return_value.close.assert_not_called()


@pytest.mark.asyncio
@patch("librouteros.async_create_transport")
async def test_async_connect_closes_transport_on_failed_login(transport_mock):
    failed = Mock(name="failed", side_effect=TrapError(message="failed to login"))
    with pytest.raises(TrapError):
        await async_connect(host="127.0.0.1", username="admin", password="", login_method=failed)
    transport_mock.return_value.close.assert_awaited_once_with()


@pytest.mark.asyncio
@patch("librouteros.async_create_transport")
async def test_async_connect_does_not_close_transport_on_success(transport_mock):
    await async_connect(host="127.0.0.1", username="admin", password="", login_method=AsyncMock(name="ok"))
    transport_mock.return_value.close.assert_not_awaited()


@pytest.mark.parametrize("exc", (socket.error, socket.timeout))
@patch("librouteros.create_connection")
def test_create_connection_does_not_wrap_socket_exceptions(conn, exc):
    conn.side_effect = exc
    with pytest.raises(exc):
        create_transport(
            host="127.0.0.1",
            port=234,
            timeout=2,
            saddr=None,
        )


@pytest.mark.asyncio
@pytest.mark.parametrize("exc", (socket.error, socket.timeout))
@patch("librouteros.asyncio.open_connection")
async def test_async_create_connection_does_not_wrap_socket_exceptions(conn, exc):
    conn.side_effect = exc
    with pytest.raises(exc):
        await async_create_transport(
            host="127.0.0.1",
            port=234,
            timeout=2,
            saddr=None,
        )
