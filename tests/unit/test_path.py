# -*- coding: UTF-8 -*-
from unittest.mock import (
    MagicMock,
)
from librouteros.api import (
    Api,
    Path,
)
from librouteros.query import Query


def test_api_path_returns_Path():
    api = Api(protocol=MagicMock())
    new = api.path("ip", "address")
    assert new.path == "/ip/address"
    assert new.api == api
    assert isinstance(new, Path)


class Test_Path:

    def setup_method(self):
        self.path = Path(
            path="/interface",
            api=MagicMock(),
        )

    def test_path_str(self):
        assert str(self.path) == self.path.path

    def test_join_single_param(self):
        assert self.path.join("ethernet").path == self.path.path + "/ethernet"

    def test_join_multi_param(self):
        assert self.path.join("ethernet", "print").path == self.path.path + "/ethernet/print"

    def test_join_rstrips_slash(self):
        assert self.path.join("ethernet", "print/").path == self.path.path + "/ethernet/print"

    def test_select_returns_Query(self):
        new = self.path.select("disabled", "name")
        assert isinstance(new, Query)

    def test_select_Query_has_valid_attributes(self):
        new = self.path.select("disabled", "name")
        assert new.api == self.path.api
        assert new.path == self.path
        assert new.keys == ("disabled", "name")

    def test_remove(self):
        self.path.remove("*1", "*2", "*3")
        self.path.api.assert_called_once_with("/interface/remove", **{".id": "*1,*2,*3"})
        # Check if returned generator was consumed
        assert self.path.api.return_value.__iter__.call_count == 1

    def test_add(self):
        self.path.api.return_value = ({
            "ret": "*1"
        }, )
        new = {"interface": "ether1", "address": "172.1.1.1/24"}
        new_id = self.path.add(**new)
        self.path.api.assert_called_once_with("/interface/add", **new)
        assert new_id == "*1"

    def test_update(self):
        args = {"name": "wan", ".id": "*1"}
        self.path.update(**args)
        self.path.api.assert_called_once_with("/interface/set", **args)
        # Check if returned generator was consumed
        assert self.path.api.return_value.__iter__.call_count == 1

    def test_iter(self):
        items = ({".id": "*1"}, {".id": "*2"})
        self.path.api.return_value = items
        new_items = tuple(self.path)
        assert new_items == items
        self.path.api.assert_called_once_with("/interface/print")

    def test_call(self):
        self.path.path = "/system/script"
        tuple(self.path("run"))
        self.path.api.assert_called_once_with("/system/script/run")
        # Check if returned generator was consumed
        assert self.path.api.return_value.__iter__.call_count == 1
