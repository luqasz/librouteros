# -*- coding: UTF-8 -*-
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from librouteros.query import (
    Query,
    Key,
    And,
    Or,
    AsyncQuery,
)


class Test_Query:
    def setup_method(self):
        self.query = Query(
            path=MagicMock(),
            api=MagicMock(),
            keys=MagicMock(),
        )
        self.async_query = AsyncQuery(
            path=MagicMock(),
            api=MagicMock(),
            keys=MagicMock(),
        )

    def test_after_init_query_is_empty_tuple(self):
        assert self.query.query == tuple()
        assert self.async_query.query == tuple()

    def test_where_returns_self(self):
        assert self.query.where() == self.query
        assert self.async_query.where() == self.async_query

    def test_where_chains_from_args(self):
        self.query.where((1, 2, 3), (4, 5))
        assert self.query.query == (1, 2, 3, 4, 5)

        self.async_query.where((1, 2, 3), (4, 5))
        assert self.async_query.query == (1, 2, 3, 4, 5)

    @patch("librouteros.query.iter")
    def test_iter_with_proplist(self, iter_mock):
        self.query.keys = ("name", "disabled")
        self.query.query = ("key1", "key2")
        iter(self.query)
        self.query.api.rawCmd.assert_called_once_with(
            str(self.query.path.join.return_value),
            "=.proplist=name,disabled",
            "key1",
            "key2",
        )

    def test_iter_with_proplist_async(self):
        self.async_query.keys = ("name", "disabled")
        self.async_query.query = ("key1", "key2")
        self.async_query.__aiter__()
        self.async_query.api.rawCmd.assert_called_once_with(
            str(self.async_query.path.join.return_value),
            "=.proplist=name,disabled",
            "key1",
            "key2",
        )

    @patch("librouteros.query.iter")
    def test_iter_no_proplist(self, iter_mock):
        self.query.keys = ()
        self.query.query = ("key1", "key2")
        iter(self.query)
        self.query.api.rawCmd.assert_called_once_with(
            str(self.query.path.join.return_value),
            "key1",
            "key2",
        )

    def test_iter_no_proplist_async(self):
        self.async_query.keys = ()
        self.async_query.query = ("key1", "key2")
        self.async_query.__aiter__()
        self.async_query.api.rawCmd.assert_called_once_with(
            str(self.async_query.path.join.return_value),
            "key1",
            "key2",
        )


class Test_Key:
    def setup_method(self):
        self.key = Key(
            name="key_name",
        )

    @pytest.mark.parametrize(
        "param, expected",
        (
            (True, "yes"),
            (False, "no"),
            ("yes", "yes"),
            (1, "1"),
        ),
    )
    def test_eq(self, param, expected):
        result = tuple(self.key == param)[0]
        assert result == "?=key_name={}".format(expected)

    def test_ne(self):
        assert tuple(self.key != 1) == ("?=key_name=1", "?#!")

    @pytest.mark.parametrize(
        "param, expected",
        (
            (True, "yes"),
            (False, "no"),
            ("yes", "yes"),
            (1, "1"),
        ),
    )
    def test_lt(self, param, expected):
        result = tuple(self.key < param)[0]
        assert result == "?<key_name={}".format(expected)

    @pytest.mark.parametrize(
        "param, expected",
        (
            (True, "yes"),
            (False, "no"),
            ("yes", "yes"),
            (1, "1"),
        ),
    )
    def test_gt(self, param, expected):
        result = tuple(self.key > param)[0]
        assert result == "?>key_name={}".format(expected)


def test_And():
    assert tuple(
        And(
            (1,),
            (2,),
            (3,),
            (4,),
        )
    ) == (1, 2, 3, 4, "?#&", "?#&", "?#&")


def test_Or():
    assert tuple(
        Or(
            (1,),
            (2,),
            (3,),
            (4,),
        )
    ) == (1, 2, 3, 4, "?#|", "?#|", "?#|")
