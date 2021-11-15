# -*- coding: UTF-8 -*-
import typing


class LibRouterosError(Exception):
    """Base exception for all other."""


class ConnectionClosed(LibRouterosError):
    """Raised when connection have been closed."""


class ProtocolError(LibRouterosError):
    """Raised when e.g. encoding/decoding fails."""


class FatalError(ProtocolError):
    """Exception raised when !fatal is received."""


class TrapError(ProtocolError):
    """
    Exception raised when !trap is received.

    :param int category: Optional integer representing category.
    :param str message: Error message.
    """

    def __init__(self, message: str, category: typing.Union[None, int] = None):
        self.category = category
        self.message = message
        super().__init__()

    def __str__(self) -> str:
        return str(self.message.replace('\r\n', ','))

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self})'


class MultiTrapError(ProtocolError):
    """
    Exception raised when multiple !trap words have been received in one response.

    :param traps: TrapError instances.
    """

    def __init__(self, *traps: TrapError):
        self.traps = traps
        super().__init__()

    def __str__(self) -> str:
        return ', '.join(str(trap) for trap in self.traps)
