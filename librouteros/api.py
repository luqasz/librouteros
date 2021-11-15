# -*- coding: UTF-8 -*-

import typing
from posixpath import join as pjoin
from librouteros.exceptions import TrapError, MultiTrapError
from librouteros.protocol import (
    compose_word,
    parse_word,
    ApiProtocol,
)
from librouteros import query

from librouteros.types import (
    ReplyDict,
    ResponseIter,
    Response,
)


class Api:

    def __init__(self, protocol: ApiProtocol):
        self.protocol = protocol

    def __call__(self, cmd: str, **kwargs: typing.Any) -> ResponseIter:
        """
        Call Api with given command.
        Yield each row.

        :param cmd: Command word. eg. /ip/address/print
        :param kwargs: Dictionary with optional arguments.
        """
        words = (compose_word(key, value) for key, value in kwargs.items())
        self.protocol.writeSentence(cmd, *words)
        yield from self.readResponse()

    def rawCmd(self, cmd: str, *words: str) -> ResponseIter:
        """
        Call Api with given command and raw words.
        End user is responsible to properly format each api word argument.
        :param cmd: Command word. eg. /ip/address/print
        :param args: Iterable with optional plain api arguments.
        """
        self.protocol.writeSentence(cmd, *words)
        yield from self.readResponse()

    def readSentence(self) -> typing.Tuple[str, ReplyDict]:
        """
        Read one sentence and parse words.

        :returns: Reply word, dict with attribute words.
        """
        reply_word, words = self.protocol.readSentence()
        return reply_word, dict(parse_word(word) for word in words)

    def readResponse(self) -> Response:
        """
        Yield each sentence untill !done is received.

        :throws TrapError: If one !trap is received.
        :throws MultiTrapError: If > 1 !trap is received.
        """
        traps = []
        reply_word = None
        response = []
        while reply_word != '!done':
            reply_word, words = self.readSentence()
            if reply_word == '!trap':
                traps.append(TrapError(**words))
            elif reply_word in ('!re', '!done') and words:
                response.append(words)

        if len(traps) > 1:
            raise MultiTrapError(*traps)
        if len(traps) == 1:
            raise traps[0]
        return response

    def close(self) -> None:
        self.protocol.close()

    def path(self, *path: str):
        return Path(
            path='',
            api=self,
        ).join(*path)


class Path:
    """Represents absolute command path."""

    def __init__(self, path: str, api: Api):
        self.path = path
        self.api = api

    def select(self, key: query.Key, *other: query.Key) -> query.Query:
        keys = (key, ) + other
        return query.Query(path=self, keys=keys, api=self.api)

    def __str__(self) -> str:
        return self.path

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self}>"

    def __iter__(self) -> ResponseIter:
        yield from self('print')

    def __call__(self, cmd: str, **kwargs: typing.Any) -> ResponseIter:
        yield from self.api(
            self.join(cmd).path,
            **kwargs,
        )

    def join(self, *path: str):
        """Join current path with one or more path strings."""
        return Path(
            api=self.api,
            path=pjoin('/', self.path, *path).rstrip('/'),
        )

    def remove(self, *ids: str) -> None:
        joined = ','.join(ids)
        tuple(self(
            'remove',
            **{'.id': joined},
        ))

    def add(self, **kwargs: typing.Any) -> str:
        ret = self(
            'add',
            **kwargs,
        )
        return tuple(ret)[0]['ret']

    def update(self, **kwargs: typing.Any) -> None:
        tuple(self(
            'set',
            **kwargs,
        ))
