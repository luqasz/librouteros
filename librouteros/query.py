# -*- coding: UTF-8 -*-
from itertools import chain
import librouteros


class Key:

    def __init__(self, name):
        self.name = name

    def __eq__(self, other):
        yield '?={}={}'.format(self, librouteros.api.Composer.pythonCast(other))

    def __ne__(self, other):
        for expr in self == other:
            yield expr
        yield '?#!'

    def __lt__(self, other):
        yield '?<{}={}'.format(self, librouteros.api.Composer.pythonCast(other))

    def __gt__(self, other):
        yield '?>{}={}'.format(self, librouteros.api.Composer.pythonCast(other))

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
    for expr in e1:
        yield expr
    for expr in e2:
        yield expr
    for e in rest:
        for expr in e:
            yield expr
    yield '?#&'
    for expr in ('?#&',) * len(rest):
        yield expr


def Or(e1, e2, *rest):
    for expr in e1:
        yield expr
    for expr in e2:
        yield expr
    for e in rest:
        for expr in e:
            yield expr
    yield '?#|'
    for expr in ('?#|',) * len(rest):
        yield expr
