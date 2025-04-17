# -*- coding: UTF-8 -*-

import typing
from logging import getLogger, NullHandler

from librouteros.exceptions import (
    ProtocolError,
    FatalError,
)
from librouteros.connections import SocketTransport, AsyncSocketTransport
import asyncio

LOGGER = getLogger("librouteros")
LOGGER.addHandler(NullHandler())

# big is network byte order
API_BYTE_ORDER = "big"


def parse_word(word: str) -> typing.Tuple[str, typing.Any]:
    """
    Split given attribute word to key, value pair.

    Values are casted to python equivalents.

    :param word: API word.
    :returns: Key, value pair.
    """
    mapping = {"yes": True, "true": True, "no": False, "false": False}
    _, key, value = word.split("=", 2)
    try:
        value = int(value)  # type: ignore
    except ValueError:
        value = mapping.get(value, value)  # type: ignore
    return (key, value)


def cast_to_api(value: typing.Any) -> str:
    """Cast python equivalent to API."""
    mapping = {True: "yes", False: "no"}
    # Required because 1 == True, 0 == False
    if type(value) == int:  # noqa: E721
        return str(value)
    return mapping.get(value, str(value))


def compose_word(key: str, value: typing.Any) -> str:
    """
    Create a attribute word from key, value pair.
    Values are casted to api equivalents.
    """
    return f"={key}={cast_to_api(value)}"


def encode_sentence(encoding: str, *words: str) -> bytes:
    """
    Encode given sentence in API format.

    :param words: Words to encode.
    :returns: Encoded sentence.
    """
    encoded = b"".join(encode_word(encoding, word) for word in words)
    # append EOS (end of sentence) byte
    encoded += b"\x00"
    return encoded


def encode_word(encoding: str, word: str) -> bytes:
    """
    Encode word in API format.

    :param word: Word to encode.
    :returns: Encoded word.
    """
    encoded_word = word.encode(encoding=encoding, errors="strict")  # type: ignore
    return encode_length(len(encoded_word)) + encoded_word


def encode_length(length: int) -> bytes:
    """
    Encode given length in mikrotik api format.

    :param length: Integer < 0x10000000
    :returns: Encoded length
    """
    if length < 0x80:
        return length.to_bytes(1, API_BYTE_ORDER)  # type: ignore[arg-type]
    elif length < 0x4000:
        val = length | 0x8000
        return val.to_bytes(2, API_BYTE_ORDER)  # type: ignore[arg-type]
    elif length < 0x200000:
        val = length | 0xC00000
        return val.to_bytes(3, API_BYTE_ORDER)  # type: ignore[arg-type]
    elif length < 0x10000000:
        val = length | 0xE0000000
        return val.to_bytes(4, API_BYTE_ORDER)  # type: ignore[arg-type]
    else:
        raise ProtocolError(f"Unable to encode length {length!r}")


def decode_length(length: bytes) -> int:
    """
    Decode api length based on given bytes.

    :param length: Bytes string to decode
    :return: Decoded length
    """
    ctl_byte = length[0]

    if ctl_byte < 0x80:
        return int.from_bytes(length, API_BYTE_ORDER)  # type: ignore[arg-type]
    elif ctl_byte < 0xC0:
        val = int.from_bytes(length[:2], API_BYTE_ORDER)  # type: ignore[arg-type]
        return val ^ 0x8000
    elif ctl_byte < 0xE0:
        val = int.from_bytes(length[:3], API_BYTE_ORDER)  # type: ignore[arg-type]
        return val ^ 0xC00000
    elif ctl_byte < 0xF0:
        val = int.from_bytes(length[:4], API_BYTE_ORDER)  # type: ignore[arg-type]
        return val ^ 0xE0000000
    else:
        raise ProtocolError(f"Unable to decode length {length!r}")


def determine_length(length: bytes) -> int:
    """
    Given first read byte, determine how many more bytes
    needs to be known in order to get fully encoded length.

    :param length: First read byte.
    :return: How many bytes to read.
    """
    ctl_byte = length[0]

    if ctl_byte < 128:
        return 0
    elif ctl_byte < 192:
        return 1
    elif ctl_byte < 224:
        return 2
    elif ctl_byte < 240:
        return 3

    raise ProtocolError(f"Unknown controll byte {length!r}")


def log(direction_string: str, *sentence: str) -> None:
    for word in sentence:
        LOGGER.debug(f"{direction_string} {word!r}")
    LOGGER.debug(f"{direction_string} EOS")


class ApiProtocol:
    def __init__(self, transport: SocketTransport, encoding: str):
        self.transport = transport
        self.encoding = encoding

    def writeSentence(self, cmd: str, *words: str) -> None:
        """
        Write encoded sentence.

        :param cmd: Command word.
        :param words: Additional words.
        """
        encoded = encode_sentence(self.encoding, cmd, *words)
        log("<---", cmd, *words)
        self.transport.write(encoded)

    def readSentence(self) -> typing.Tuple[str, typing.Tuple[str, ...]]:
        """
        Read every word until empty word (NULL byte) is received.

        :return: Reply word, tuple with read words.
        """
        sentence = tuple(word for word in iter(self.readWord, ""))
        log("--->", *sentence)
        reply_word, words = sentence[0], sentence[1:]
        if reply_word == "!fatal":
            self.transport.close()
            raise FatalError(words[0])
        return reply_word, words

    def readWord(self) -> str:
        byte = self.transport.read(1)
        # Early return check for null byte
        if byte == b"\x00":
            return ""
        to_read = determine_length(byte)
        byte += self.transport.read(to_read)
        length = decode_length(byte)
        word = self.transport.read(length)
        return word.decode(encoding=self.encoding, errors="ignore")

    def close(self) -> None:
        self.transport.close()


class AsyncApiProtocol:
    def __init__(self, transport: AsyncSocketTransport, encoding: str, timeout: typing.Optional[float] = None):
        self.transport = transport
        self.encoding = encoding
        self.timeout = timeout

    async def writeSentence(self, cmd: str, *words: str) -> None:
        """
        Write encoded sentence.

        :param cmd: Command word.
        :param words: Additional words.
        """
        encoded = encode_sentence(self.encoding, cmd, *words)
        log("<---", cmd, *words)
        await asyncio.wait_for(self.transport.write(encoded), self.timeout)

    async def readSentence(self) -> typing.Tuple[str, typing.Tuple[str, ...]]:
        """
        Read every word until empty word (NULL byte) is received.

        :return: Reply word, tuple with read words.
        """

        async def inner():
            sentence = []
            while True:
                word = await self.readWord()
                if word == "":
                    break
                sentence.append(word)
            return tuple(sentence)

        sentence = await asyncio.wait_for(inner(), self.timeout)
        log("--->", *sentence)
        reply_word, words = sentence[0], sentence[1:]
        if reply_word == "!fatal":
            await self.transport.close()
            raise FatalError(words[0])
        return reply_word, tuple(words)

    async def readWord(self) -> str:
        byte = await self.transport.read(1)
        # Early return check for null byte
        if byte == b"\x00":
            return ""
        to_read = determine_length(byte)
        byte += await self.transport.read(to_read)
        length = decode_length(byte)
        word = await self.transport.read(length)
        return word.decode(encoding=self.encoding, errors="ignore")

    async def close(self) -> None:
        await self.transport.close()
