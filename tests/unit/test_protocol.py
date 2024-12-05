# -*- coding: UTF-8 -*-

import pytest
from unittest.mock import MagicMock, patch

from librouteros.protocol import Encoder, Decoder, ApiProtocol, AsyncApiProtocol
from librouteros.connections import SocketTransport, AsyncSocketTransport
from librouteros.exceptions import (
    ProtocolError,
    FatalError,
)


class Test_Decoder:
    def setup_method(self):
        self.decoder = Decoder()
        self.decoder.encoding = "ASCII"

    @pytest.mark.parametrize(
        "length,expected",
        (
            (b"x", 0),  # 120
            (b"\xbf", 1),  # 191
            (b"\xdf", 2),  # 223
            (b"\xef", 3),  # 239
        ),
    )
    def test_determineLength(self, length, expected):
        assert self.decoder.determineLength(length) == expected

    def test_determineLength_raises(self, bad_first_length_bytes):
        with pytest.raises(ProtocolError) as error:
            self.decoder.determineLength(bad_first_length_bytes)
        assert str(bad_first_length_bytes) in str(error.value)

    def test_decodeLength(self, valid_word_length):
        result = self.decoder.decodeLength(valid_word_length.encoded)
        assert result == valid_word_length.integer

    def test_decodeLength_raises(self, bad_length_bytes):
        with pytest.raises(ProtocolError) as error:
            self.decoder.decodeLength(bad_length_bytes)
        assert str(bad_length_bytes) in str(error.value)


class Test_Encoder:
    def setup_method(self):
        self.encoder = Encoder()
        self.encoder.encoding = "ASCII"

    def test_encodeLength(self, valid_word_length):
        result = self.encoder.encodeLength(valid_word_length.integer)
        assert result == valid_word_length.encoded

    def test_encodeLength_raises_if_lenghth_is_too_big(self):
        """Length must be < 268435456"""
        invalid = 268435456
        with pytest.raises(ProtocolError):
            self.encoder.encodeLength(invalid)

    def test_non_ASCII_word_encoding(self):
        """When encoding is ASCII, word may only contain ASCII characters."""
        self.encoder.encoding = "ASCII"
        with pytest.raises(UnicodeEncodeError):
            self.encoder.encodeWord("łą")

    @patch.object(Encoder, "encodeLength", return_value=b"")
    def test_utf_8_word_encoding(self, enc_len_mock):
        """
        Assert that len is taken from bytes, not utf8 word itself.

        len('ł') == 1
        'ł'.encode(encoding='UTF8') == 2
        """
        self.encoder.encoding = "utf-8"
        word = "ł"
        self.encoder.encodeWord(word)
        enc_len_mock.assert_called_once_with(len(word.encode(self.encoder.encoding)))

    @patch.object(Encoder, "encodeWord", return_value=b"")
    def test_encodeSentence(self, encodeWord_mock):
        r"""
        Assert that:
            \x00 is appended to the sentence
            encodeWord is called == len(sentence)
        """
        encoded = self.encoder.encodeSentence("first", "second")
        assert encodeWord_mock.call_count == 2
        assert encoded[-1:] == b"\x00"


class Test_ApiProtocol:
    def setup_method(self):
        self.protocol = ApiProtocol(
            transport=MagicMock(spec=SocketTransport),
            encoding="utf-8",
        )
        self.async_protocol = AsyncApiProtocol(
            transport=MagicMock(spec=AsyncSocketTransport),
            encoding="utf-8",
        )

    @pytest.mark.asyncio
    @patch.object(Encoder, "encodeSentence")
    async def test_writeSentence_calls_encodeSentence(self, encodeSentence_mock):
        self.protocol.writeSentence("/ip/address/print", "=key=value")
        encodeSentence_mock.assert_called_once_with("/ip/address/print", "=key=value")

        # async
        await self.async_protocol.writeSentence("/ip/address/print", "=key=value")
        encodeSentence_mock.assert_called_with("/ip/address/print", "=key=value")

    @pytest.mark.asyncio
    @patch.object(Encoder, "encodeSentence")
    async def test_writeSentence_calls_transport_write(self, encodeSentence_mock):
        """Assert that write is called with encoded sentence."""
        self.protocol.writeSentence("/ip/address/print", "=key=value")
        self.protocol.transport.write.assert_called_once_with(encodeSentence_mock.return_value)

        # async
        await self.async_protocol.writeSentence("/ip/address/print", "=key=value")
        self.async_protocol.transport.write.assert_called_once_with(encodeSentence_mock.return_value)

    @pytest.mark.asyncio
    @patch("librouteros.protocol.iter", return_value=("!fatal", "reason"))
    async def test_readSentence_raises_FatalError(self, iter_mock):
        """Assert that FatalError is raised with its reason."""
        with pytest.raises(FatalError) as error:
            self.protocol.readSentence()
        assert str(error.value) == "reason"
        assert self.protocol.transport.close.call_count == 1

    @pytest.mark.asyncio
    @patch("librouteros.protocol.AsyncApiProtocol.readWord", side_effect=["!fatal", "reason", ""])
    async def test_async_readSentence_raises_FatalError(self, readWord_mock):
        """Assert that FatalError is raised with its reason."""
        with pytest.raises(FatalError) as error:
            await self.async_protocol.readSentence()
        assert str(error.value) == "reason"
        assert self.async_protocol.transport.close.call_count == 1

    @pytest.mark.asyncio
    async def test_decoding_ignores_character_errors(self):
        word = b"\x11\xfb\x95" + "łąć".encode("utf-8")
        length = Encoder.encodeLength(len(word))
        self.protocol.transport.read.side_effect = (length, b"", word)
        assert self.protocol.readWord() == "\x11łąć"

        # async
        self.async_protocol.transport.read.side_effect = (length, b"", word)
        assert await self.async_protocol.readWord() == "\x11łąć"

    @pytest.mark.asyncio
    async def test_close(self):
        self.protocol.close()
        self.protocol.transport.close.assert_called_once_with()

        # async
        await self.async_protocol.close()
        self.async_protocol.transport.close.assert_called_once_with()
