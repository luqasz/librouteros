# -*- coding: UTF-8 -*-
from itertools import chain


class RowItem:

    def __init__(self, name):
        self.name = name

    def __eq__(self, other):
        yield '?={}={}'.format(self, other)

    def __ne__(self, other):
        yield from self == other
        yield '?#!'

    def __lt__(self, other):
        yield '?<{}={}'.format(self, other)

    def __gt__(self, other):
        yield '?>{}={}'.format(self, other)

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
        query = ('=.proplist={}'.format(keys),)
        query += self.query
        return iter(self.api.rawCmd(str(self.path) + '/print', *query))

    # def Having(self, item):
    #     self._query += ('?{}'.format(item),)
    #     return self
    #
    # def NotHaving(self, item):
    #     self._query += ('?-{}'.format(item),)
    #     return self


def And(e1, e2):
    yield from e1
    yield from e2
    yield '?#&'


def Or(e1, e2):
    yield from e1
    yield from e2
    yield '?#|'


class Path:

    def __init__(self, path, api):
        self.path = path
        self.api = api

    def select(self, *keys):
        return Query(path=self, keys=keys, api=self.api)

    def __str__(self):
        return str(self.path)

    def __repr__(self):
        return "<{module}.{cls} {path!r}>".format(
            module=self.__class__.__module__,
            cls=self.__class__.__name__,
            path=self.path,
        )
