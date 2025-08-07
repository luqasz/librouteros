from collections import namedtuple
from struct import pack

import pytest

WordLength = namedtuple("WordLength", ("integer", "encoded"))
WordPair = namedtuple("WordPair", ("word", "pair"))


@pytest.fixture(scope="function")
def bad_length_bytes():
    """len(length) must be < 5"""
    return b"\xff\xff\xff\xff\xff"


@pytest.fixture(
    scope="function",
    params=(
        WordLength(integer=0, encoded=b"\x00"),
        WordLength(integer=127, encoded=b"\x7f"),
        WordLength(integer=130, encoded=b"\x80\x82"),
        WordLength(integer=2097140, encoded=b"\xdf\xff\xf4"),
        WordLength(integer=268435440, encoded=b"\xef\xff\xff\xf0"),
    ),
)
def valid_word_length(request):
    return request.param


@pytest.fixture(scope="function", params=(pack(">B", i) for i in range(240, 256)))
def bad_first_length_bytes(request):
    """First byte of length must be < 240."""
    return request.param


@pytest.fixture(
    params=(
        WordPair(word="=key=yes", pair=("key", True)),
        WordPair(word="=key=no", pair=("key", False)),
        WordPair(word="=key=string", pair=("key", "string")),
        WordPair(word="=key=none", pair=("key", "none")),
        WordPair(word="=key=22.2", pair=("key", "22.2")),
        WordPair(word="=key=22", pair=("key", 22)),
        WordPair(word="=key=0", pair=("key", 0)),
    )
)
def word_pair(request):
    """Words and key,value pairs used for casting from/to python/api in both directions."""
    return request.param


@pytest.fixture(
    params=(
        (
            ("!empty", {}),
            ("!empty", {}),
            ("!done", {}),
        ),
        (
            ("!empty", {}),
            ("!re", {}),
            ("!done", {}),
        ),
        (
            ("!re", {}),
            ("!done", {}),
        ),
    )
)
def empty_response(request):
    return request.param
