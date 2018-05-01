# -*- coding: UTF-8 -*-


class RowItem:

    def __init__(self, name, path):
        self.path = path
        self.name = name

    def __eq__(self, other):
        self.path._query += ('?={}={}'.format(self, other), )

    def __ne__(self, other):
        self == other
        self.path._query += ('?#!',)

    def __lt__(self, other):
        self.path._query += ('?<{}={}'.format(self, other), )

    def __gt__(self, other):
        self.path._query += ('?>{}={}'.format(self, other), )
        return self

    def __str__(self):
        return str(self.name)


class CommandPath:

    def __init__(self):
        self._args = dict()
        self._query = tuple()

    def Having(self, item):
        self._query += ('?{}'.format(item),)
        return self

    def NotHaving(self, item):
        self._query += ('?-{}'.format(item),)
        return self

    def __getitem__(self, item):
        return RowItem(name=item, path=self)
