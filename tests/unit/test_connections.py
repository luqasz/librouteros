# -*- coding: UTF-8 -*-

import socket
from asyncio import StreamReader, StreamWriter
from unittest.mock import MagicMock

import pytest

from librouteros.connections import AsyncSocketTransport, SocketTransport
from librouteros.exceptions import (
    ConnectionClosed,
)


class Test_SocketTransport:
    def setup_method(self):
        self.transport = SocketTransport(sock=MagicMock(spec=socket.socket))

    def test_close_shutdown_exception(self):
        self.transport.sock.shutdown.side_effect = socket.error
        self.transport.close()
        self.transport.sock.close.assert_called_once_with()

    def test_close(self):
        self.transport.close()
        self.transport.sock.close.assert_called_once_with()

    def test_calls_sendall(self):
        self.transport.write(b"some message")
        self.transport.sock.sendall.assert_called_once_with(b"some message")

    def test_read_raises_when_recv_returns_empty_byte_string(self):
        self.transport.sock.recv.return_value = b""
        with pytest.raises(ConnectionClosed):
            self.transport.read(3)

    def test_read_reads_full_length(self):
        """
        Check if read() reads all data, even when socket.recv()
        needs to be called multiple times.
        """
        self.transport.sock.recv.side_effect = (b"retu", b"rne", b"d")
        assert self.transport.read(8) == b"returned"

    @pytest.mark.parametrize("exception", (socket.error, socket.timeout))
    def test_recv_raises_socket_errors(self, exception):
        self.transport.sock.recv.side_effect = exception
        with pytest.raises(exception):
            self.transport.read(2)


class Test_AsyncSocketTransport:
    def setup_method(self):
        self.transport = AsyncSocketTransport(
            reader=MagicMock(spec=StreamReader),
            writer=MagicMock(spec=StreamWriter),
        )

    @pytest.mark.asyncio
    async def test_close(self):
        await self.transport.close()
        self.transport.writer.close.assert_called_once_with()

    @pytest.mark.asyncio
    async def test_write(self):
        await self.transport.write(b"some message")
        self.transport.writer.write.assert_called_once_with(b"some message")
        self.transport.writer.drain.assert_called_once_with()

    @pytest.mark.asyncio
    async def test_read_raises_when_recv_returns_empty_byte_string(self):
        self.transport.reader.read.return_value = b""
        with pytest.raises(ConnectionClosed):
            await self.transport.read(3)

    @pytest.mark.asyncio
    async def test_read_reads_full_length(self):
        """
        Check if read() reads all data, even when socket.recv()
        needs to be called multiple times.
        """
        self.transport.reader.read.side_effect = (b"retu", b"rne", b"d")
        assert await self.transport.read(8) == b"returned"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("exception", (socket.error, socket.timeout))
    async def test_recv_raises_socket_errors(self, exception):
        self.transport.reader.read.side_effect = exception
        with pytest.raises(exception):
            await self.transport.read(2)
