# -*- coding: UTF-8 -*-
import typing
from itertools import chain
from librouteros.protocol import (
    cast_to_api,
)
from librouteros.types import (
    QueryGen,
    ResponseIter,
)


class Key:
    def __init__(self, name: str):
        self.name = name

    def __eq__(self, other):
        yield f"?={self}={cast_to_api(other)}"

    def __ne__(self, other):
        yield from self == other
        yield "?#!"

    def __lt__(self, other):
        yield f"?<{self}={cast_to_api(other)}"

    def __gt__(self, other):
        yield f"?>{self}={cast_to_api(other)}"

    def __str__(self) -> str:
        return str(self.name)

    # pylint: disable=invalid-name
    def In(self, one, *elems):
        yield from self == one
        yield from chain.from_iterable(self == str(elem) for elem in elems)
        yield from ("?#|",) * len(elems)


class Query:
    def __init__(self, path, keys: typing.Sequence[Key], api):
        self.path = path
        self.keys = keys
        self.api = api
        self.query: typing.Tuple[str, ...] = tuple()

    def where(self, *args: str):
        self.query = tuple(chain.from_iterable(args))
        return self

    def __iter__(self) -> ResponseIter:
        cmd = str(self.path.join("print"))
        words = tuple(self.query)
        if len(self.keys) > 0:
            keys = ",".join(str(key) for key in self.keys)
            keys = f"=.proplist={keys}"
            words = (keys,) + words
        return iter(self.api.rawCmd(cmd, *words))


def And(left: QueryGen, right: QueryGen, *rest: QueryGen) -> QueryGen:
    # pylint: disable=invalid-name
    yield from left
    yield from right
    yield from chain.from_iterable(rest)
    yield "?#&"
    yield from ("?#&",) * len(rest)


def Or(left: QueryGen, right: QueryGen, *rest: QueryGen) -> QueryGen:
    # pylint: disable=invalid-name
    yield from left
    yield from right
    yield from chain.from_iterable(rest)
    yield "?#|"
    yield from ("?#|",) * len(rest)


class AsyncQuery:
    def __init__(self, path, keys: typing.Sequence[Key], api):
        self.path = path
        self.keys = keys
        self.api = api
        self.query: typing.Tuple[str, ...] = tuple()

    def where(self, *args: str):
        self.query = tuple(chain.from_iterable(args))
        return self

    def __aiter__(self):
        cmd = str(self.path.join("print"))
        words = tuple(self.query)
        if len(self.keys) > 0:
            keys = ",".join(str(key) for key in self.keys)
            keys = f"=.proplist={keys}"
            words = (keys,) + words
        return self.api.rawCmd(cmd, *words)

    def __iter__(self):
        raise AttributeError("Use 'async for' instead of 'for' to iterate over Query results.")
