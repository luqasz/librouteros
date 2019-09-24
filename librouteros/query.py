# -*- coding: UTF-8 -*-
from itertools import chain
from librouteros.protocol import (
        pyCast,
        )


class Key:

    def __init__(self, name):
        self.name = name

    def __eq__(self, other):
        yield '?={}={}'.format(self, pyCast(other))

    def __ne__(self, other):
        yield from self == other
        yield '?#!'

    def __lt__(self, other):
        yield '?<{}={}'.format(self, pyCast(other))

    def __gt__(self, other):
        yield '?>{}={}'.format(self, pyCast(other))

    def __str__(self):
        return str(self.name)


class Query:

    def __init__(self, path, keys, api):
        self.path = path
        self.keys = keys
        self.api = api
        self.query = tuple()

    def where(self, *args):
        self.query = tuple(chain.from_iterable(args))
        return self

    def __iter__(self):
        keys = ','.join(str(key) for key in self.keys)
        keys = '=.proplist={}'.format(keys)
        cmd = str(self.path.join('print'))
        return iter(self.api.rawCmd(cmd, keys, *self.query))


def And(e1, e2, *rest):
    yield from e1
    yield from e2
    yield from chain.from_iterable(rest)
    yield '?#&'
    yield from ('?#&',) * len(rest)


def Or(e1, e2, *rest):
    yield from e1
    yield from e2
    yield from chain.from_iterable(rest)
    yield '?#|'
    yield from ('?#|',) * len(rest)
