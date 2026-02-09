# -*- coding: UTF-8 -*-

from unittest.mock import (
    AsyncMock,
    Mock,
)

import pytest

from librouteros.api import (
    Api,
    AsyncApi,
)
from librouteros.protocol import (
    compose_word,
    parse_word,
)


@pytest.mark.parametrize(
    ("word", "pair"),
    (
        ("=dynamic=true", ("dynamic", True)),
        ("=dynamic=false", ("dynamic", False)),
    ),
)
def test_bool_parse_word(word, pair):
    """
    Test for parsing legacy bool values.

    Older routeros versions accept yes/true/no/false as values,
    but only return true/false.
    """
    assert parse_word(word) == pair


def test_parse_word(word_pair):
    assert parse_word(word_pair.word) == word_pair.pair


def test_compose_word(word_pair):
    assert compose_word(*word_pair.pair) == word_pair.word


def test_read_empty_sentences(empty_response):
    api = Api(protocol=Mock())
    api.readSentence = Mock(side_effect=empty_response)
    assert len(api.readResponse()) == 0


@pytest.mark.asyncio
async def test_async_read_empty_sentences(empty_response):
    api = AsyncApi(protocol=AsyncMock())
    api.readSentence = AsyncMock(side_effect=empty_response)
    assert len(await api.readResponse()) == 0


def test_api_call_kwargs_colison():
    """
    Assert that:
        TypeError: Api.__call__() got multiple values for argument 'cmd'
    Is not raised.
    """
    api = Api(protocol=Mock())
    api("/ip/address/print", **{"cmd": 123})


def test_async_api_call_kwargs_colison():
    """
    Assert that:
        TypeError: Api.__call__() got multiple values for argument 'cmd'
    Is not raised.
    """
    api = AsyncApi(protocol=Mock())
    api("/ip/address/print", **{"cmd": 123})


def test_api_path_call_kwargs_colison():
    """
    Assert that:
        TypeError: Api.__call__() got multiple values for argument 'cmd'
    Is not raised.
    """
    api = Api(protocol=Mock())
    path = api.path("/ip/address")
    path("print", **{"cmd": 123})


def test_async_api_path_call_kwargs_colison():
    """
    Assert that:
        TypeError: Api.__call__() got multiple values for argument 'cmd'
    Is not raised.
    """
    api = AsyncApi(protocol=Mock())
    path = api.path("/ip/address")
    path("print", **{"cmd": 123})
