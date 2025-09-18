# -*- coding: UTF-8 -*-
from asyncio import StreamReader, StreamWriter
from socket import socket

from librouteros.exceptions import ConnectionClosed


class SocketTransport:
    def __init__(self, sock: socket):
        self.sock = sock

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
        data = bytearray()
        while (to_read := length - len(data)) != 0:
            got = self.sock.recv(to_read)
            if not got:
                raise ConnectionClosed("Connection unexpectedly closed.")
            data += got
        return data

    def close(self) -> None:
        self.sock.close()


class AsyncSocketTransport:
    def __init__(self, reader: StreamReader, writer: StreamWriter):
        self.reader = reader
        self.writer = writer

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
        data = bytearray()
        while (to_read := length - len(data)) != 0:
            got = await self.reader.read(to_read)
            if not got:
                raise ConnectionClosed("Connection unexpectedly closed.")
            data += got
        return data

    async def close(self) -> None:
        self.writer.close()
        await self.writer.wait_closed()
