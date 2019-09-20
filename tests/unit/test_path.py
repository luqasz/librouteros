# -*- coding: UTF-8 -*-
import pytest
from mock import (
        Mock,
        patch,
        )
from librouteros.api import (
        Api,
        Path,
        )


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
