# -*- coding: UTF-8 -*-

import pytest
from socket import error as SOCKET_ERROR, timeout as SOCKET_TIMEOUT, socket
from mock import MagicMock, patch, call

from librouteros import connections
from librouteros.exceptions import ConnectionError, FatalError


class Test_Decoder:

    def setup(self):
        self.decoder = connections.Decoder()
        self.decoder.encoding = 'ASCII'

    @pytest.mark.parametrize("length,expected", (
        (b'x', 0),  # 120
        (b'\xbf', 1),  # 191
        (b'\xdf', 2),  # 223
        (b'\xef', 3),  # 239
        ))
    def test_determineLength(self, length, expected):
        assert self.decoder.determineLength(length) == expected

    def test_determineLength_raises(self, bad_first_length_bytes):
        with pytest.raises(ConnectionError) as error:
            self.decoder.determineLength(bad_first_length_bytes)
        assert str(bad_first_length_bytes) in str(error.value)

    def test_decodeLength(self, valid_word_length):
        result = self.decoder.decodeLength(valid_word_length.encoded)
        assert result == valid_word_length.integer

    def test_decodeLength_raises(self, bad_length_bytes):
        with pytest.raises(ConnectionError) as error:
            self.decoder.decodeLength(bad_length_bytes)
        assert str(bad_length_bytes) in str(error.value)


class Test_Encoder:

    def setup(self):
        self.encoder = connections.Encoder()
        self.encoder.encoding = 'ASCII'

    def test_encodeLength(self, valid_word_length):
        result = self.encoder.encodeLength(valid_word_length.integer)
        assert result == valid_word_length.encoded

    def test_encodeLength_raises_if_lenghth_is_too_big(self, bad_length_int):
        with pytest.raises(ConnectionError) as error:
            self.encoder.encodeLength(bad_length_int)
        assert str(bad_length_int) in str(error.value)

    @patch.object(connections.Encoder, 'encodeLength', return_value=b'len_')
    def test_encodeWord(self, encodeLength_mock):
        assert self.encoder.encodeWord('word') == b'len_word'
        assert encodeLength_mock.call_count == 1

    def test_non_ASCII_word_encoding(self):
        """When encoding is ASCII, word may only contain ASCII characters."""
        self.encoder.encoding = 'ASCII'
        with pytest.raises(UnicodeEncodeError):
            self.encoder.encodeWord(u'łą')

    def test_utf_8_word_encoding(self):
        """Assert that utf-8 encoding works."""
        self.encoder.encoding = 'utf-8'
        assert self.encoder.encodeWord(u'łą').endswith(b'\xc5\x82\xc4\x85')

    @patch.object(connections.Encoder, 'encodeWord', return_value=b'')
    def test_encodeSentence(self, encodeWord_mock):
        r"""
        Assert that:
            \x00 is appended to the sentence
            encodeWord is called == len(sentence)
        """
        encoded = self.encoder.encodeSentence('first', 'second')
        assert encodeWord_mock.call_count == 2
        assert encoded[-1:] == b'\x00'


class Test_ApiProtocol:

    def setup(self):
        self.protocol = connections.ApiProtocol(
                transport=MagicMock(spec=connections.SocketTransport),
                encoding='ASCII',
                )

    @patch.object(connections.Encoder, 'encodeSentence')
    def test_writeSentence_calls_encodeSentence(self, encodeSentence_mock):
        self.protocol.writeSentence('/ip/address/print', '=key=value')
        encodeSentence_mock.assert_called_once_with('/ip/address/print', '=key=value')

    @patch.object(connections.Encoder, 'encodeSentence')
    def test_writeSentence_calls_transport_write(self, encodeSentence_mock):
        """Assert that write is called with encoded sentence."""
        self.protocol.writeSentence('/ip/address/print', '=key=value')
        self.protocol.transport.write.assert_called_once_with(encodeSentence_mock.return_value)

    @patch('librouteros.connections.iter', return_value=('!fatal', 'reason'))
    def test_readSentence_raises_FatalError(self, iter_mock):
        """Assert that FatalError is raised with its reason."""
        with pytest.raises(FatalError) as error:
            self.protocol.readSentence()
        assert str(error.value) == 'reason'
        assert self.protocol.transport.close.call_count == 1

    def test_close(self):
        self.protocol.close()
        self.protocol.transport.close.assert_called_once_with()


class Test_SocketTransport:

    def setup(self):
        self.transport = connections.SocketTransport(sock=MagicMock(spec=socket))

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
