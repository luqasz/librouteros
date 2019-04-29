# -*- coding: UTF-8 -*-

import pytest
from mock import MagicMock

from librouteros.api import (
        Api,
        )
from librouteros.protocol import (
        parseWord,
        composeWord,
        )


@pytest.mark.parametrize('word,pair', (
            ('=dynamic=true', ('dynamic', True)),
            ('=dynamic=false', ('dynamic', False)),
        ))
def test_bool_parseWord(word, pair):
    """
    Test for parsing legacy bool values.

    Older routeros versions accept yes/true/no/false as values,
    but only return true/false.
    """
    assert parseWord(word) == pair


def test_parseWord(word_pair):
    assert parseWord(word_pair.word) == word_pair.pair


def test_composeWord(word_pair):
    assert composeWord(*word_pair.pair) == word_pair.word


class Test_Api:

    def setup(self):
        self.api = Api(protocol=MagicMock())

    @pytest.mark.parametrize("path, expected", (
        ("/ip/address/", "/ip/address"),
        ("ip/address", "/ip/address"),
        ("/ip/address", "/ip/address"),
        ))
    def test_joinPath_single_param(self, path, expected):
        assert self.api.joinPath(path) == expected

    @pytest.mark.parametrize("path, expected", (
        (("/ip/address/", "print"), "/ip/address/print"),
        (("ip/address", "print"), "/ip/address/print"),
        (("/ip/address", "set"), "/ip/address/set"),
        (("/", "/ip/address", "set"), "/ip/address/set"),
        ))
    def test_joinPath_multi_param(self, path, expected):
        assert self.api.joinPath(*path) == expected
