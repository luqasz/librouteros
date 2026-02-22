# -*- coding: UTF-8 -*-

from __future__ import annotations

from collections.abc import Iterator, Sequence
from itertools import chain
from typing import TYPE_CHECKING

from librouteros.protocol import (
    cast_to_api,
)
from librouteros.types import (
    AsyncResponseIter,
    QueryGen,
    ResponseIter,
)

if TYPE_CHECKING:
    from librouteros.api import Api, AsyncApi, AsyncPath, Path


class Key:
    def __init__(self, name: str) -> None:
        self.name: str = name

    def __eq__(self, other) -> Iterator[str]:  # type: ignore ; magic method
        yield f"?={self}={cast_to_api(other)}"

    def __ne__(self, other) -> Iterator[str]:  # type: ignore ; magic method
        yield from self == other
        yield "?#!"

    def __lt__(self, other) -> Iterator[str]:
        yield f"?<{self}={cast_to_api(other)}"

    def __gt__(self, other) -> Iterator[str]:
        yield f"?>{self}={cast_to_api(other)}"

    def __str__(self) -> str:
        return str(self.name)

    def In(self, one, *elems) -> Iterator[str]:  # noqa: N802
        yield from self == one
        yield from chain.from_iterable(self == str(elem) for elem in elems)
        yield from ("?#|",) * len(elems)


class Query:
    def __init__(self, path: Path, keys: Sequence[Key], api: Api) -> None:
        self.path: Path = path
        self.keys: Sequence[Key] = keys
        self.api: Api = api
        self.query: tuple[str, ...] = ()

    def where(self, *args: str) -> "Query":
        self.query = tuple(chain.from_iterable(args))
        return self

    def __iter__(self) -> ResponseIter:
        cmd: str = str(self.path.join("print"))
        words: tuple[str, ...] = tuple(self.query)
        if len(self.keys) > 0:
            keys: str = ",".join(str(key) for key in self.keys)
            keys = f"=.proplist={keys}"
            words: tuple[str, ...] = (keys, *words)
        return iter(self.api.rawCmd(cmd, *words))


def And(left: QueryGen, right: QueryGen, *rest: QueryGen) -> QueryGen:  # noqa N802
    yield from left
    yield from right
    yield from chain.from_iterable(rest)
    yield "?#&"
    yield from ("?#&",) * len(rest)


def Or(left: QueryGen, right: QueryGen, *rest: QueryGen) -> QueryGen:  # noqa N802
    yield from left
    yield from right
    yield from chain.from_iterable(rest)
    yield "?#|"
    yield from ("?#|",) * len(rest)


class AsyncQuery:
    def __init__(self, path: AsyncPath, keys: Sequence[Key], api: AsyncApi) -> None:
        self.path: AsyncPath = path
        self.keys: Sequence[Key] = keys
        self.api: AsyncApi = api
        self.query: tuple[str, ...] = ()

    def where(self, *args: str) -> "AsyncQuery":
        self.query = tuple(chain.from_iterable(args))
        return self

    def __aiter__(self) -> AsyncResponseIter:
        cmd: str = str(self.path.join("print"))
        words: tuple[str, ...] = tuple(self.query)
        if len(self.keys) > 0:
            keys: str = ",".join(str(key) for key in self.keys)
            keys = f"=.proplist={keys}"
            words: tuple[str, ...] = (keys, *words)
        return self.api.rawCmd(cmd, *words)

    def __iter__(self) -> None:
        raise AttributeError("Use 'async for' instead of 'for' to iterate over Query results.")
