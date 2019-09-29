# -*- coding: UTF-8 -*-
from unittest.mock import (
    Mock,
)
from librouteros.api import (
    Api,
    Path,
)
from librouteros.query import Query


def test_api_path_returns_Path():
    api = Api(protocol=Mock())
    new = api.path('ip', 'address')
    assert new.path == '/ip/address'
    assert new.api == api
    assert isinstance(new, Path)


class Test_Path:

    def setup(self):
        self.path = Path(
            path='/interface',
            api=Mock(),
        )

    def test_path_str(self):
        assert str(self.path) == self.path.path

    def test_join_single_param(self):
        assert self.path.join('ethernet').path == self.path.path + '/ethernet'

    def test_join_multi_param(self):
        assert self.path.join('ethernet', 'print').path == self.path.path + '/ethernet/print'

    def test_join_rstrips_slash(self):
        assert self.path.join('ethernet', 'print/').path == self.path.path + '/ethernet/print'

    def test_select_returns_Query(self):
        new = self.path.select('disabled', 'name')
        assert type(new) == Query

    def test_select_Query_has_valid_attributes(self):
        new = self.path.select('disabled', 'name')
        assert new.api == self.path.api
        assert new.path == self.path
        assert new.keys == ('disabled', 'name')
