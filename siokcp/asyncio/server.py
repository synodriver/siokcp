# -*- coding: utf-8 -*-
import asyncio
from functools import partial
from typing import Any, Callable, Dict, Optional

from siokcp._kcp import KCPConnection, getconv
from siokcp.asyncio.transport import KCPTransport

# todo updater: 定期调用connection.check 和 connection.update, 把state==-1的kcptransport关闭，掉用他们的protocol.connection_lost，从kcp_transports中删除
class BaseKCPServerProtocol(asyncio.DatagramProtocol):
    def __init__(self, protocol_factory, log: Callable[[str], Any], loop=None):
        self.protocol_factory = protocol_factory
        self.kcp_transports = {}  # type: Dict[int, KCPTransport]
        self._log = log
        self._loop = loop or asyncio.get_running_loop()
        self._close_waiter = self._loop.create_future()
        self._drain_waiter = asyncio.Event()
        self._drain_waiter.set()

    def connection_made(self, transport: asyncio.DatagramTransport) -> None:
        self.transport = transport

    def connection_lost(self, exc: Optional[Exception]) -> None:
        self.transport = None
        for conv, kcp_transport in self.kcp_transports.items():
            kcp_transport.get_protocol().connection_lost(exc)
        if exc is not None:
            self._close_waiter.set_exception(exc)
        else:
            self._close_waiter.set_result(None)
        self._drain_waiter.set()

    def pause_writing(self) -> None:
        try:
            self.transport.pause_reading()
        except AttributeError:
            pass
        self._drain_waiter.clear()

    def resume_writing(self) -> None:
        try:
            self.transport.resume_reading()
        except AttributeError:
            pass
        self._drain_waiter.set()

    def datagram_received(self, data: bytes, addr):
        """Called when some datagram is received."""
        conv: int = getconv(data)
        if conv not in self.kcp_transports:
            protocol = (
                self.protocol_factory()
            )  # 对于每个新虚拟连接 调用一次protocol_factory

            connection = KCPConnection(conv, partial(self._send, addr=addr), self._log)
            kcp_transport = KCPTransport(
                connection, self.transport, protocol, self._loop
            )  # 虚拟层
            self.kcp_transports[conv] = kcp_transport

            connection.receive_data(data)
            packet: bytes = connection.next_event()
            connection.flush()

            protocol.data_received(packet)
        else:
            kcp_transport = self.kcp_transports[conv]
            protocol = kcp_transport.get_protocol()
            kcp_transport.connection.receive_data(data)
            packet: bytes = kcp_transport.connection.next_event()
            kcp_transport.connection.flush()
            protocol.data_received(packet)
        # kcp_transport._connection.receive_data(data)
        # packet: bytes = kcp_transport._connection.next_event()
        # kcp_transport._connection.flush()
        # self.packet_received(conv, packet)

    def error_received(self, exc):
        """Called when a send or receive operation raises an OSError.

        (Other than BlockingIOError or InterruptedError.)
        """
        # todo close all connections

    async def aclose(self):
        for conv, kcp_transport in self.kcp_transports.items():
            kcp_transport.close()
        await self.drain()
        self.transport.close()
        await self._close_waiter

    async def drain(self):
        await self._drain_waiter.wait()

    def _send(self, data: bytes, addr):
        self.transport.sendto(data, addr)

    async def send(self, conv: int, data: bytes):
        kcp_transport = self.kcp_transports.get(conv, None)
        if kcp_transport is None:
            raise ValueError(f"connection {conv} not found")
        kcp_transport.connection.send(data)
        kcp_transport.connection.flush()
        await self.drain()


_DEFAULT_LIMIT = 2**16  # 64 KiB


async def create_kcp_server(
    loop,
    protocol_factory,
    local_addr,
    log: Callable[[str], Any],
    remote_addr: tuple[str, int] | str | None = None,
    *,
    family: int = 0,
    proto: int = 0,
    flags: int = 0,
    reuse_address: bool | None = None,
    reuse_port: bool | None = None,
    allow_broadcast: bool | None = None,
    sock=None,
):
    await loop.create_datagram_endpoint(
        lambda: BaseKCPServerProtocol(protocol_factory, log, loop),
        local_addr,
        remote_addr,
        family,
        proto,
        flags,
        reuse_address,
        reuse_port,
        allow_broadcast,
        sock,
    )


async def start_kcp_server(
    client_connected_cb, local_addr, log: Callable[[str], Any], *, limit=_DEFAULT_LIMIT, **kwds
):
    loop = asyncio.get_running_loop()

    def factory():
        reader = asyncio.StreamReader(limit=limit, loop=loop)
        protocol = asyncio.StreamReaderProtocol(reader, client_connected_cb, loop=loop)
        return protocol

    return await create_kcp_server(loop, factory, local_addr, log, **kwds)
