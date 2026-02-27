# -*- coding: UTF-8 -*-

from asyncio import StreamReader, StreamWriter
from socket import socket

from librouteros.exceptions import ConnectionClosed


class SocketTransport:
    def __init__(self, sock: socket) -> None:
        self.sock: socket = sock

    def write(self, data: bytes) -> None:
        """
        Write given bytes to socket. Loop as long as every byte in
        string is written unless exception is raised.
        """
        self.sock.sendall(data)

    def read(self, length: int) -> bytes:
        """
        Read as many bytes from socket as specified in length.
        Loop as long as every byte is read unless exception is raised.
        """
        data: bytearray = bytearray()
        while (to_read := length - len(data)) != 0:
            got: bytes = self.sock.recv(to_read)
            if not got:
                raise ConnectionClosed("Connection unexpectedly closed.")
            data += got
        return bytes(data)

    def close(self) -> None:
        self.sock.close()


class AsyncSocketTransport:
    def __init__(self, reader: StreamReader, writer: StreamWriter) -> None:
        self.reader: StreamReader = reader
        self.writer: StreamWriter = writer

    async def write(self, data: bytes) -> None:
        """
        Write given bytes to socket. Loop as long as every byte in
        string is written unless exception is raised.
        """
        self.writer.write(data)
        await self.writer.drain()

    async def read(self, length: int) -> bytes:
        """
        Read as many bytes from socket as specified in length.
        Loop as long as every byte is read unless exception is raised.
        """
        data: bytearray = bytearray()
        while (to_read := length - len(data)) != 0:
            got: bytes = await self.reader.read(to_read)
            if not got:
                raise ConnectionClosed("Connection unexpectedly closed.")
            data += got
        return bytes(data)

    async def close(self) -> None:
        self.writer.close()
        await self.writer.wait_closed()
