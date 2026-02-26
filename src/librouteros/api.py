# -*- coding: UTF-8 -*-

from __future__ import annotations

from collections.abc import Generator
from posixpath import join as pjoin

from librouteros.exceptions import MultiTrapError, TrapError
from librouteros.protocol import (
    ApiProtocol,
    AsyncApiProtocol,
    compose_word,
    parse_word,
)
from librouteros.query import AsyncQuery, Key, Query
from librouteros.types import (
    AsyncResponseIter,
    ReplyDict,
    Response,
    ResponseIter,
    ROSType,
)


class Api:
    def __init__(self, protocol: ApiProtocol) -> None:
        self.protocol: ApiProtocol = protocol

    def __call__(self, cmd: str, /, **kwargs: ROSType) -> ResponseIter:
        """
        Call Api with given command.
        Yield each row.

        :param cmd: Command word. eg. /ip/address/print
        :param kwargs: Dictionary with optional arguments.
        """
        words: Generator[str] = (compose_word(key, value) for key, value in kwargs.items())
        self.protocol.writeSentence(cmd, *words)
        yield from self.readResponse()

    def rawCmd(self, cmd: str, *words: str) -> ResponseIter:  # noqa N802
        """
        Call Api with given command and raw words.
        End user is responsible to properly format each api word argument.
        :param cmd: Command word. eg. /ip/address/print
        :param args: Iterable with optional plain api arguments.
        """
        self.protocol.writeSentence(cmd, *words)
        yield from self.readResponse()

    def readSentence(self) -> tuple[str, ReplyDict]:  # noqa N802
        """
        Read one sentence and parse words.

        :returns: Reply word, dict with attribute words.
        """
        reply_word, words = self.protocol.readSentence()
        return reply_word, dict(parse_word(word) for word in words)

    def readResponse(self) -> Response:  # noqa N802
        """
        Yield each sentence untill !done is received.

        :throws TrapError: If one !trap is received.
        :throws MultiTrapError: If > 1 !trap is received.
        """
        traps: list[TrapError] = []
        reply_word: str | None = None
        response: Response = []
        while reply_word != "!done":
            reply_word, words = self.readSentence()
            if reply_word == "!trap":
                traps.append(TrapError(**words))  # type: ignore[call-arg]  # must be correct types
            elif reply_word in ("!re", "!done") and words:
                response.append(words)

        if len(traps) > 1:
            raise MultiTrapError(*traps)
        if len(traps) == 1:
            raise traps[0]
        return response

    def close(self) -> None:
        self.protocol.close()

    def path(self, *path: str) -> "Path":
        return Path(
            path="",
            api=self,
        ).join(*path)


class Path:
    """Represents absolute command path."""

    def __init__(self, path: str, api: Api) -> None:
        self.path: str = path
        self.api: Api = api

    def select(self, *keys: Key) -> Query:
        return Query(path=self, keys=keys, api=self.api)

    def __str__(self) -> str:
        return self.path

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self}>"

    def __iter__(self) -> ResponseIter:
        yield from self("print")

    def __call__(self, cmd: str, /, **kwargs: ROSType) -> ResponseIter:
        yield from self.api(
            self.join(cmd).path,
            **kwargs,
        )

    def join(self, *path: str) -> "Path":
        """Join current path with one or more path strings."""
        return Path(
            api=self.api,
            path=pjoin("/", self.path, *path).rstrip("/"),
        )

    def remove(self, *ids: str) -> None:
        joined: str = ",".join(ids)
        tuple(
            self(
                "remove",
                **{".id": joined},
            )
        )

    def add(self, **kwargs: ROSType) -> str:
        ret: ResponseIter = self(
            "add",
            **kwargs,
        )
        return str(next(iter(ret))["ret"])

    def update(self, **kwargs: ROSType) -> None:
        tuple(
            self(
                "set",
                **kwargs,
            )
        )


class AsyncApi:
    def __init__(self, protocol: AsyncApiProtocol) -> None:
        self.protocol: AsyncApiProtocol = protocol

    async def __call__(self, cmd: str, /, **kwargs: ROSType) -> AsyncResponseIter:
        """
        Call Api with given command.
        Yield each row.

        :param cmd: Command word. eg. /ip/address/print
        :param kwargs: Dictionary with optional arguments.
        """
        words: Generator[str] = (compose_word(key, value) for key, value in kwargs.items())
        await self.protocol.writeSentence(cmd, *words)
        response: Response = await self.readResponse()
        for item in response:
            yield item

    async def rawCmd(self, cmd: str, *words: str) -> AsyncResponseIter:  # noqa N802
        """
        Call Api with given command and raw words.
        End user is responsible to properly format each api word argument.
        :param cmd: Command word. eg. /ip/address/print
        :param args: Iterable with optional plain api arguments.
        """
        await self.protocol.writeSentence(cmd, *words)
        response: Response = await self.readResponse()
        for item in response:
            yield item

    async def readSentence(self) -> tuple[str, ReplyDict]:  # noqa N802
        """
        Read one sentence and parse words.
        """
        # Assuming readSentence is also an async method in the protocol
        reply_word, words = await self.protocol.readSentence()
        return reply_word, dict(parse_word(word) for word in words)

    async def readResponse(self) -> Response:  # noqa N802
        """
        Yield each sentence untill !done is received.

        :throws TrapError: If one !trap is received.
        :throws MultiTrapError: If > 1 !trap is received.
        """
        traps: list[TrapError] = []
        reply_word: str | None = None
        response: Response = []
        while reply_word != "!done":
            reply_word, words = await self.readSentence()
            if reply_word == "!trap":
                traps.append(TrapError(**words))  # type: ignore[call-arg]  # must be correct types
            elif reply_word in ("!re", "!done") and words:
                response.append(words)

        if len(traps) > 1:
            raise MultiTrapError(*traps)
        if len(traps) == 1:
            raise traps[0]
        return response

    async def close(self) -> None:
        await self.protocol.close()

    def path(self, *path: str) -> "AsyncPath":
        return AsyncPath(
            path="",
            api=self,
        ).join(*path)


class AsyncPath:
    """Represents absolute command path."""

    def __init__(self, path: str, api: AsyncApi) -> None:
        self.path: str = path
        self.api: AsyncApi = api

    def select(self, *keys: Key) -> AsyncQuery:
        return AsyncQuery(path=self, keys=keys, api=self.api)

    def __str__(self) -> str:
        return self.path

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self}>"

    async def __aiter__(self) -> AsyncResponseIter:
        async for response in self("print"):
            yield response

    async def __call__(self, cmd: str, /, **kwargs: ROSType) -> AsyncResponseIter:
        async for response in self.api(
            self.join(cmd).path,
            **kwargs,
        ):
            yield response

    def join(self, *path: str) -> "AsyncPath":
        """Join current path with one or more path strings."""
        return AsyncPath(
            api=self.api,
            path=pjoin("/", self.path, *path).rstrip("/"),
        )

    async def remove(self, *ids: str) -> None:
        joined: str = ",".join(ids)
        [
            response
            async for response in self(
                "remove",
                **{".id": joined},
            )
        ]

    async def add(self, **kwargs: ROSType) -> str:
        response: Response = [
            response
            async for response in self(
                "add",
                **kwargs,
            )
        ]
        return str(response[0]["ret"])

    async def update(self, **kwargs: ROSType) -> None:
        [
            response
            async for response in self(
                "set",
                **kwargs,
            )
        ]
