# -*- coding: UTF-8 -*-
import pytest
from mock import (MagicMock, patch)
from librouteros.query import (
    Query,
    Key,
    And,
    Or,
)


class Test_Query:

    def setup(self):
        self.query = Query(
            path=MagicMock(),
            api=MagicMock(),
            keys=MagicMock(),
        )

    def test_after_init_query_is_empty_tuple(self):
        assert self.query.query == tuple()

    def test_where_returns_self(self):
        assert self.query.where() == self.query

    def test_where_chains_from_args(self):
        self.query.where((1, 2, 3), (4, 5))
        assert self.query.query == (1, 2, 3, 4, 5)

    @patch('librouteros.query.iter')
    def test_iter_calls_api_rawCmd(self, iter_mock):
        self.query.keys = ('name', 'disabled')
        self.query.query = ('key1', 'key2')
        iter(self.query)
        self.query.api.rawCmd.assert_called_once_with(
            str(self.query.path.join.return_value),
            '=.proplist=name,disabled',
            'key1',
            'key2',
        )


class Test_Key:

    def setup(self):
        self.key = Key(name='key_name', )

    @pytest.mark.parametrize('param, expected', (
        (True, 'yes'),
        (False, 'no'),
        ('yes', 'yes'),
        (1, '1'),
    ))
    def test_eq(self, param, expected):
        result = tuple(self.key == param)[0]
        assert result == '?=key_name={}'.format(expected)

    def test_ne(self):
        assert tuple(self.key != 1) == ('?=key_name=1', '?#!')

    @pytest.mark.parametrize('param, expected', (
        (True, 'yes'),
        (False, 'no'),
        ('yes', 'yes'),
        (1, '1'),
    ))
    def test_lt(self, param, expected):
        result = tuple(self.key < param)[0]
        assert result == '?<key_name={}'.format(expected)

    @pytest.mark.parametrize('param, expected', (
        (True, 'yes'),
        (False, 'no'),
        ('yes', 'yes'),
        (1, '1'),
    ))
    def test_gt(self, param, expected):
        result = tuple(self.key > param)[0]
        assert result == '?>key_name={}'.format(expected)


def test_And():
    assert tuple(And(
        (1, ),
        (2, ),
        (3, ),
        (4, ),
    )) == (1, 2, 3, 4, '?#&', '?#&', '?#&')


def test_Or():
    assert tuple(Or(
        (1, ),
        (2, ),
        (3, ),
        (4, ),
    )) == (1, 2, 3, 4, '?#|', '?#|', '?#|')
