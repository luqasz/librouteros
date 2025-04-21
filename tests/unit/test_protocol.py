# -*- coding: UTF-8 -*-

import pytest
from unittest.mock import MagicMock, patch
from hypothesis import given, strategies as st

from librouteros.protocol import (
    ApiProtocol,
    AsyncApiProtocol,
    encode_length,
    decode_length,
    determine_length,
    encode_word,
    encode_sentence,
)
from librouteros.connections import SocketTransport, AsyncSocketTransport
from librouteros.exceptions import (
    ProtocolError,
    FatalError,
)


def test_encode_length_raises():
    """Length must be < 268435456"""
    invalid = 268435456
    with pytest.raises(ProtocolError):
        encode_length(invalid)


def test_encode_length(valid_word_length):
    result = encode_length(valid_word_length.integer)
    assert result == valid_word_length.encoded


def test_decode_length(valid_word_length):
    result = decode_length(valid_word_length.encoded)
    assert result == valid_word_length.integer


def test_decode_length_raises(bad_length_bytes):
    with pytest.raises(ProtocolError) as error:
        decode_length(bad_length_bytes)
    assert str(bad_length_bytes) in str(error.value)


@given(st.integers(0, 0x10000000 - 1))
def test_encode_decode_length(n):
    encoded = encode_length(n)
    assert decode_length(encoded) == n


@pytest.mark.parametrize(
    "length,expected",
    (
        (b"x", 0),  # 120
        (b"\xbf", 1),  # 191
        (b"\xdf", 2),  # 223
        (b"\xef", 3),  # 239
    ),
)
def test_determine_length(length, expected):
    assert determine_length(length) == expected


def test_determine_length_raises(bad_first_length_bytes):
    with pytest.raises(ProtocolError) as error:
        determine_length(bad_first_length_bytes)
    assert str(bad_first_length_bytes) in str(error.value)


@patch("librouteros.protocol.encode_length", return_value=b"")
def test_utf_8_word_encoding(enc_len_mock):
    """
    Assert that len is taken from bytes, not utf8 word itself.

    len('ł') == 1
    len('ł'.encode(encoding='UTF8')) == 2
    """
    encode_word("ł", "UTF8")  # "ł" encodes in 2 bytes
    enc_len_mock.assert_called_once_with(2)


@patch("librouteros.protocol.encode_word", return_value=b"\xff")
def test_encode_sentence(encode_word_mock):
    r"""
    Assert that:
        \x00 is appended to the sentence
        encodeWord is called == len(sentence)
    """
    encoded = encode_sentence("first", "second", encoding="UTF8")
    assert encode_word_mock.call_count == 2
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

    @patch("librouteros.protocol.encode_sentence")
    async def test_writeSentence_calls_encodeSentence(self, encodeSentence_mock):
        self.protocol.writeSentence("/ip/address/print", "=key=value")
        encodeSentence_mock.assert_called_once_with("/ip/address/print", "=key=value", encoding=self.protocol.encoding)

    @pytest.mark.asyncio
    @patch("librouteros.protocol.encode_sentence")
    async def test_async_writeSentence_calls_encodeSentence(self, encodeSentence_mock):
        await self.async_protocol.writeSentence("/ip/address/print", "=key=value")
        encodeSentence_mock.assert_called_once_with("/ip/address/print", "=key=value", encoding=self.protocol.encoding)

    @pytest.mark.asyncio
    @patch("librouteros.protocol.encode_sentence")
    async def test_writeSentence_calls_transport_write(self, encodeSentence_mock):
        """Assert that write is called with encoded sentence."""
        self.protocol.writeSentence("/ip/address/print", "=key=value")
        self.protocol.transport.write.assert_called_once_with(encodeSentence_mock.return_value)

        # async
        await self.async_protocol.writeSentence("/ip/address/print", "=key=value")
        self.async_protocol.transport.write.assert_called_once_with(encodeSentence_mock.return_value)

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
        with pytest.raises(UnicodeDecodeError):
            word.decode()
        length = encode_length(len(word))

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
