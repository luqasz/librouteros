# -*- coding: UTF-8 -*-

import pytest

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
