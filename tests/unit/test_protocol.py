# -*- coding: UTF-8 -*-

import pytest
from socket import error as SOCKET_ERROR, timeout as SOCKET_TIMEOUT, socket
from mock import MagicMock, patch, call

from librouteros.protocol import (
        Encoder,
        Decoder,
        ApiProtocol,
        )
from librouteros.connections import SocketTransport
from librouteros.exceptions import ConnectionError, FatalError


class Test_Decoder:

    def setup(self):
        self.decoder = Decoder()
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
        self.encoder = Encoder()
        self.encoder.encoding = 'ASCII'

    def test_encodeLength(self, valid_word_length):
        result = self.encoder.encodeLength(valid_word_length.integer)
        assert result == valid_word_length.encoded

    def test_encodeLength_raises_if_lenghth_is_too_big(self, bad_length_int):
        with pytest.raises(ConnectionError) as error:
            self.encoder.encodeLength(bad_length_int)
        assert str(bad_length_int) in str(error.value)

    @patch.object(Encoder, 'encodeLength', return_value=b'len_')
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

    @patch.object(Encoder, 'encodeWord', return_value=b'')
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
        self.protocol = ApiProtocol(
                transport=MagicMock(spec=SocketTransport),
                encoding='ASCII',
                )

    @patch.object(Encoder, 'encodeSentence')
    def test_writeSentence_calls_encodeSentence(self, encodeSentence_mock):
        self.protocol.writeSentence('/ip/address/print', '=key=value')
        encodeSentence_mock.assert_called_once_with('/ip/address/print', '=key=value')

    @patch.object(Encoder, 'encodeSentence')
    def test_writeSentence_calls_transport_write(self, encodeSentence_mock):
        """Assert that write is called with encoded sentence."""
        self.protocol.writeSentence('/ip/address/print', '=key=value')
        self.protocol.transport.write.assert_called_once_with(encodeSentence_mock.return_value)

    @patch('librouteros.protocol.iter', return_value=('!fatal', 'reason'))
    def test_readSentence_raises_FatalError(self, iter_mock):
        """Assert that FatalError is raised with its reason."""
        with pytest.raises(FatalError) as error:
            self.protocol.readSentence()
        assert str(error.value) == 'reason'
        assert self.protocol.transport.close.call_count == 1

    def test_close(self):
        self.protocol.close()
        self.protocol.transport.close.assert_called_once_with()
