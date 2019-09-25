# -*- coding: UTF-8 -*-

import pytest
from socket import error as SOCKET_ERROR, timeout as SOCKET_TIMEOUT, socket
from mock import MagicMock, patch, call

from librouteros.connections import SocketTransport
from librouteros.exceptions import ConnectionError, FatalError


class Test_SocketTransport:

    def setup(self):
        self.transport = SocketTransport(sock=MagicMock(spec=socket))

    def test_calls_socket_close(self):
        self.transport.close()
        self.transport.sock.close.assert_called_once()

    def test_close_shutdown_exception(self):
        self.transport.sock.shutdown.side_effect = SOCKET_ERROR
        self.transport.close()
        self.transport.sock.close.assert_called_once_with()

    def test_close(self):
        self.transport.close()
        self.transport.sock.close.assert_called_once_with()

    def test_calls_sendall(self):
        self.transport.write(b'some message')
        self.transport.sock.sendall.assert_called_once_with(b'some message')

    @pytest.mark.parametrize("exception", (SOCKET_ERROR, SOCKET_TIMEOUT))
    def test_write_raises_socket_errors(self, exception):
        self.transport.sock.sendall.side_effect = exception
        with pytest.raises(exception):
            self.transport.write(b'some data')

    def test_read_raises_when_recv_returns_empty_byte_string(self):
        self.transport.sock.recv.return_value = b''
        with pytest.raises(ConnectionError):
            self.transport.read(3)

    def test_read_reads_full_length(self):
        """
        Check if read() reads all data, even when socket.recv()
        needs to be called multiple times.
        """
        self.transport.sock.recv.side_effect = (b'retu', b'rne', b'd')
        assert self.transport.read(8) == b'returned'
        # Check if we ask only for what is left after each recv()
        assert self.transport.sock.recv.call_args_list == [
                call(8),
                call(4),
                call(1),
                ]

    @pytest.mark.parametrize("exception", (SOCKET_ERROR, SOCKET_TIMEOUT))
    def test_recv_raises_socket_errors(self, exception):
        self.transport.sock.recv.side_effect = exception
        with pytest.raises(exception):
            self.transport.read(2)
