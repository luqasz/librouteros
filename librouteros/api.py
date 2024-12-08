# -*- coding: UTF-8 -*-

import typing
from posixpath import join as pjoin
from librouteros.exceptions import TrapError, MultiTrapError
from librouteros.protocol import (
    compose_word,
    parse_word,
    ApiProtocol,
    AsyncApiProtocol,
)
from librouteros import query

from librouteros.types import (
    ReplyDict,
    ResponseIter,
    AsyncResponseIter,
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
        while reply_word != "!done":
            reply_word, words = self.readSentence()
            if reply_word == "!trap":
                traps.append(TrapError(**words))
            elif reply_word in ("!re", "!done") and words:
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
            path="",
            api=self,
        ).join(*path)


class Path:
    """Represents absolute command path."""

    def __init__(self, path: str, api: Api):
        self.path = path
        self.api = api

    def select(self, *keys: query.Key) -> query.Query:
        return query.Query(path=self, keys=keys, api=self.api)

    def __str__(self) -> str:
        return self.path

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self}>"

    def __iter__(self) -> ResponseIter:
        yield from self("print")

    def __call__(self, cmd: str, **kwargs: typing.Any) -> ResponseIter:
        yield from self.api(
            self.join(cmd).path,
            **kwargs,
        )

    def join(self, *path: str):
        """Join current path with one or more path strings."""
        return Path(
            api=self.api,
            path=pjoin("/", self.path, *path).rstrip("/"),
        )

    def remove(self, *ids: str) -> None:
        joined = ",".join(ids)
        tuple(
            self(
                "remove",
                **{".id": joined},
            )
        )

    def add(self, **kwargs: typing.Any) -> str:
        ret = self(
            "add",
            **kwargs,
        )
        return tuple(ret)[0]["ret"]

    def update(self, **kwargs: typing.Any) -> None:
        tuple(
            self(
                "set",
                **kwargs,
            )
        )


class AsyncApi:
    def __init__(self, protocol: AsyncApiProtocol):
        self.protocol = protocol

    async def __call__(self, cmd: str, **kwargs: typing.Any) -> AsyncResponseIter:
        """
        Call Api with given command.
        Yield each row.

        :param cmd: Command word. eg. /ip/address/print
        :param kwargs: Dictionary with optional arguments.
        """
        words = (compose_word(key, value) for key, value in kwargs.items())
        await self.protocol.writeSentence(cmd, *words)
        response = await self.readResponse()
        for item in response:
            yield item

    async def rawCmd(self, cmd: str, *words: str) -> AsyncResponseIter:
        """
        Call Api with given command and raw words.
        End user is responsible to properly format each api word argument.
        :param cmd: Command word. eg. /ip/address/print
        :param args: Iterable with optional plain api arguments.
        """
        await self.protocol.writeSentence(cmd, *words)
        response = await self.readResponse()
        for item in response:
            yield item

    async def readSentence(self) -> typing.Tuple[str, ReplyDict]:
        """
        Read one sentence and parse words.
        """
        # Assuming readSentence is also an async method in the protocol
        reply_word, words = await self.protocol.readSentence()
        return reply_word, dict(parse_word(word) for word in words)

    async def readResponse(self) -> Response:
        """
        Yield each sentence untill !done is received.

        :throws TrapError: If one !trap is received.
        :throws MultiTrapError: If > 1 !trap is received.
        """
        traps = []
        reply_word = None
        response = []
        while reply_word != "!done":
            reply_word, words = await self.readSentence()
            if reply_word == "!trap":
                traps.append(TrapError(**words))
            elif reply_word in ("!re", "!done") and words:
                response.append(words)

        if len(traps) > 1:
            raise MultiTrapError(*traps)
        if len(traps) == 1:
            raise traps[0]
        return response

    async def close(self) -> None:
        await self.protocol.close()

    def path(self, *path: str):
        return AyncPath(
            path="",
            api=self,
        ).join(*path)


class AyncPath:
    """Represents absolute command path."""

    def __init__(self, path: str, api: AsyncApi):
        self.path = path
        self.api = api

    def select(self, *keys: query.Key) -> query.AsyncQuery:
        return query.AsyncQuery(path=self, keys=keys, api=self.api)

    def __str__(self) -> str:
        return self.path

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self}>"

    async def __aiter__(self) -> AsyncResponseIter:
        async for response in self("print"):
            yield response

    async def __call__(self, cmd: str, **kwargs: typing.Any) -> AsyncResponseIter:
        async for response in self.api(
            self.join(cmd).path,
            **kwargs,
        ):
            yield response

    def join(self, *path: str):
        """Join current path with one or more path strings."""
        return AyncPath(
            api=self.api,
            path=pjoin("/", self.path, *path).rstrip("/"),
        )

    async def remove(self, *ids: str) -> None:
        joined = ",".join(ids)
        [
            response
            async for response in self(
                "remove",
                **{".id": joined},
            )
        ]

    async def add(self, **kwargs: typing.Any) -> str:
        response = [
            response
            async for response in self(
                "add",
                **kwargs,
            )
        ]
        return response[0]["ret"]

    async def update(self, **kwargs: typing.Any) -> None:
        [
            response
            async for response in self(
                "set",
                **kwargs,
            )
        ]
