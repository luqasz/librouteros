# -*- coding: UTF-8 -*-
from unittest.mock import MagicMock

import pytest

from librouteros.api import Api, AsyncApi, AsyncPath, Path
from librouteros.query import AsyncQuery, Query


def test_api_path_returns_Path():
    api = Api(protocol=MagicMock())
    new = api.path("ip", "address")
    assert new.path == "/ip/address"
    assert new.api == api
    assert isinstance(new, Path)


def test_async_api_path_returns_AsyncPath():
    api = AsyncApi(protocol=MagicMock())
    new = api.path("ip", "address")
    assert new.path == "/ip/address"
    assert new.api == api
    assert isinstance(new, AsyncPath)


class Test_Path:
    def setup_method(self):
        self.path = Path(
            path="/interface",
            api=MagicMock(),
        )
        self.async_path = AsyncPath(
            path="/interface",
            api=MagicMock(),
        )

    def test_path_str(self):
        assert str(self.path) == self.path.path
        assert str(self.async_path) == self.async_path.path

    def test_join_single_param(self):
        assert self.path.join("ethernet").path == self.path.path + "/ethernet"
        assert self.async_path.join("ethernet").path == self.async_path.path + "/ethernet"

    def test_join_multi_param(self):
        assert self.path.join("ethernet", "print").path == self.path.path + "/ethernet/print"
        assert self.async_path.join("ethernet", "print").path == self.async_path.path + "/ethernet/print"

    def test_join_rstrips_slash(self):
        assert self.path.join("ethernet", "print/").path == self.path.path + "/ethernet/print"
        assert self.async_path.join("ethernet", "print/").path == self.async_path.path + "/ethernet/print"

    def test_select_returns_Query(self):
        new = self.path.select("disabled", "name")
        assert isinstance(new, Query)
        new = self.async_path.select("disabled", "name")
        assert isinstance(new, AsyncQuery)

    def test_select_Query_has_valid_attributes(self):
        new = self.path.select("disabled", "name")
        assert new.api == self.path.api
        assert new.path == self.path
        assert new.keys == ("disabled", "name")
        new = self.async_path.select("disabled", "name")
        assert new.api == self.async_path.api
        assert new.path == self.async_path
        assert new.keys == ("disabled", "name")

    @pytest.mark.asyncio
    async def test_remove(self):
        self.path.remove("*1", "*2", "*3")
        self.path.api.assert_called_once_with("/interface/remove", **{".id": "*1,*2,*3"})
        # Check if returned generator was consumed
        assert self.path.api.return_value.__iter__.call_count == 1
        await self.async_path.remove("*1", "*2", "*3")
        self.async_path.api.assert_called_once_with("/interface/remove", **{".id": "*1,*2,*3"})
        # Check if returned generator was consumed
        assert self.async_path.api.return_value.__aiter__.call_count == 1

    @pytest.mark.asyncio
    async def test_add(self):
        return_value = ({"ret": "*1"},)
        self.path.api.return_value = return_value
        new = {"interface": "ether1", "address": "172.1.1.1/24"}

        new_id = self.path.add(**new)
        self.path.api.assert_called_once_with("/interface/add", **new)
        assert new_id == "*1"

        # async
        # mock async iterable
        async def mock_api(*args, **kwargs):
            for item in return_value:
                yield item

        self.async_path.api.side_effect = mock_api
        new_id = await self.async_path.add(**new)
        self.async_path.api.assert_called_once_with("/interface/add", **new)
        assert new_id == "*1"

    @pytest.mark.asyncio
    async def test_update(self):
        args = {"name": "wan", ".id": "*1"}
        self.path.update(**args)
        self.path.api.assert_called_once_with("/interface/set", **args)
        # Check if returned generator was consumed
        assert self.path.api.return_value.__iter__.call_count == 1

        await self.async_path.update(**args)
        self.async_path.api.assert_called_once_with("/interface/set", **args)
        assert self.async_path.api.return_value.__aiter__.call_count == 1

    @pytest.mark.asyncio
    async def test_iter(self):
        items = ({".id": "*1"}, {".id": "*2"})
        self.path.api.return_value = items
        new_items = tuple(self.path)
        assert new_items == items
        self.path.api.assert_called_once_with("/interface/print")

        # async
        # mock async iterable
        async def mock_api(*args, **kwargs):
            for item in items:
                yield item

        self.async_path.api.side_effect = mock_api
        new_items = tuple([r async for r in self.async_path])
        assert new_items == items
        self.async_path.api.assert_called_once_with("/interface/print")

    @pytest.mark.asyncio
    async def test_call(self):
        self.path.path = "/system/script"
        tuple(self.path("run"))
        self.path.api.assert_called_once_with("/system/script/run")
        # Check if returned generator was consumed
        assert self.path.api.return_value.__iter__.call_count == 1

        # Async
        self.async_path.path = "/system/script"
        [r async for r in self.async_path("run")]
        self.async_path.api.assert_called_once_with("/system/script/run")
        # Check if returned generator was consumed
        assert self.async_path.api.return_value.__aiter__.call_count == 1

    def test_select_without_keys(self):
        query = self.path.select()
        assert isinstance(query, Query)

        # Async
        query = self.async_path.select()
        assert isinstance(query, AsyncQuery)
