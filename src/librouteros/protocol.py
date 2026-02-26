# -*- coding: UTF-8 -*-

import asyncio
from logging import NullHandler, getLogger
from typing import Final, Literal

from librouteros.connections import AsyncSocketTransport, SocketTransport
from librouteros.exceptions import (
    FatalError,
    ProtocolError,
)
from librouteros.types import ROSType

LOGGER = getLogger("librouteros")
LOGGER.addHandler(NullHandler())

# big is network byte order
API_BYTE_ORDER: Final[Literal["big"]] = "big"


def parse_word(word: str) -> tuple[str, ROSType]:
    """
    Split given attribute word to key, value pair.

    Values are casted to python equivalents.

    :param word: API word.
    :returns: Key, value pair.
    """
    mapping: dict[str, bool] = {"yes": True, "true": True, "no": False, "false": False}
    _, key, value = word.split("=", 2)
    try:
        ros_value: ROSType = int(value)
    except ValueError:
        ros_value = mapping.get(value, value)
    return (key, ros_value)


def cast_to_api(value: ROSType) -> str:
    """Cast python equivalent to API."""
    mapping: dict[ROSType, str] = {True: "yes", False: "no"}
    # Required because 1 == True, 0 == False
    if type(value) == int:  # noqa E721
        return str(value)
    return mapping.get(value, str(value))


def compose_word(key: str, value: ROSType) -> str:
    """
    Create a attribute word from key, value pair.
    Values are casted to api equivalents.
    """
    return f"={key}={cast_to_api(value)}"


def encode_sentence(*words: str, encoding: str) -> bytes:
    """
    Encode given sentence in API format.

    :param words: Words to encode.
    :returns: Encoded sentence.
    """
    encoded: bytes = b"".join(encode_word(word, encoding) for word in words)
    # append EOS (end of sentence) byte
    encoded += b"\x00"
    return encoded


def encode_word(word: str, encoding: str) -> bytes:
    """
    Encode word in API format.

    :param word: Word to encode.
    :returns: Encoded word.
    """
    encoded_word: bytes = word.encode(encoding=encoding, errors="strict")
    return encode_length(len(encoded_word)) + encoded_word


def encode_length(length: int) -> bytes:
    """
    Encode given length in mikrotik api format.

    :param length: Integer < 0x10000000
    :returns: Encoded length
    """
    if length < 0x80:
        return length.to_bytes(1, API_BYTE_ORDER)
    elif length < 0x4000:
        val = length | 0x8000
        return val.to_bytes(2, API_BYTE_ORDER)
    elif length < 0x200000:
        val = length | 0xC00000
        return val.to_bytes(3, API_BYTE_ORDER)
    elif length < 0x10000000:
        val = length | 0xE0000000
        return val.to_bytes(4, API_BYTE_ORDER)
    else:
        raise ProtocolError(f"Unable to encode length {length!r}")


def decode_length(length: bytes) -> int:
    """
    Decode api length based on given bytes.

    :param length: Bytes string to decode
    :return: Decoded length
    """
    ctl_byte: int = length[0]

    if ctl_byte < 0x80:
        return int.from_bytes(length, API_BYTE_ORDER)
    elif ctl_byte < 0xC0:
        val = int.from_bytes(length[:2], API_BYTE_ORDER)
        return val ^ 0x8000
    elif ctl_byte < 0xE0:
        val = int.from_bytes(length[:3], API_BYTE_ORDER)
        return val ^ 0xC00000
    elif ctl_byte < 0xF0:
        val = int.from_bytes(length[:4], API_BYTE_ORDER)
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
    ctl_byte: int = length[0]

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
    def __init__(self, transport: SocketTransport, encoding: str) -> None:
        self.transport: SocketTransport = transport
        self.encoding: str = encoding

    def writeSentence(self, cmd: str, *words: str) -> None:  # noqa N802
        """
        Write encoded sentence.

        :param cmd: Command word.
        :param words: Additional words.
        """
        encoded: bytes = encode_sentence(cmd, *words, encoding=self.encoding)
        log("<---", cmd, *words)
        self.transport.write(encoded)

    def readSentence(self) -> tuple[str, tuple[str, ...]]:  # noqa N802
        """
        Read every word until empty word (NULL byte) is received.

        :return: Reply word, tuple with read words.
        """
        sentence: tuple[str, ...] = tuple(word for word in iter(self.readWord, ""))
        log("--->", *sentence)
        reply_word, words = sentence[0], sentence[1:]
        if reply_word == "!fatal":
            self.transport.close()
            raise FatalError(words[0])
        return reply_word, words

    def readWord(self) -> str:  # noqa N802
        byte: bytes = self.transport.read(1)
        # Early return check for null byte
        if byte == b"\x00":
            return ""
        to_read: int = determine_length(byte)
        byte += self.transport.read(to_read)
        length: int = decode_length(byte)
        word: bytes = self.transport.read(length)
        return word.decode(encoding=self.encoding, errors="ignore")

    def close(self) -> None:
        self.transport.close()


class AsyncApiProtocol:
    def __init__(self, transport: AsyncSocketTransport, encoding: str, timeout: float | None = None):
        self.transport: AsyncSocketTransport = transport
        self.encoding: str = encoding
        self.timeout: float | None = timeout

    async def writeSentence(self, cmd: str, *words: str) -> None:  # noqa N802
        """
        Write encoded sentence.

        :param cmd: Command word.
        :param words: Additional words.
        """
        encoded: bytes = encode_sentence(cmd, *words, encoding=self.encoding)
        log("<---", cmd, *words)
        await asyncio.wait_for(self.transport.write(encoded), self.timeout)

    async def readSentence(self) -> tuple[str, tuple[str, ...]]:  # noqa N802
        """
        Read every word until empty word (NULL byte) is received.

        :return: Reply word, tuple with read words.
        """

        async def inner() -> tuple[str, ...]:
            sentence: list[str] = []
            while (word := await self.readWord()) != "":
                sentence.append(word)
            return tuple(sentence)

        sentence: tuple[str, ...] = await asyncio.wait_for(inner(), self.timeout)
        log("--->", *sentence)
        reply_word, words = sentence[0], sentence[1:]
        if reply_word == "!fatal":
            await self.transport.close()
            raise FatalError(words[0])
        return reply_word, tuple(words)

    async def readWord(self) -> str:  # noqa N802
        byte: bytes = await self.transport.read(1)
        # Early return check for null byte
        if byte == b"\x00":
            return ""
        to_read: int = determine_length(byte)
        byte += await self.transport.read(to_read)
        length: int = decode_length(byte)
        word: bytes = await self.transport.read(length)
        return word.decode(encoding=self.encoding, errors="ignore")

    async def close(self) -> None:
        await self.transport.close()
