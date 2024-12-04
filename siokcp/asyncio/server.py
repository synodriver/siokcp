# -*- coding: utf-8 -*-
import asyncio
import time
from functools import partial
from typing import Any, Awaitable, Callable, Dict, Optional, Set, Tuple, Union

from siokcp._kcp import KCPConnection, getconv
from siokcp.asyncio.transport import KCPTransport
from siokcp.asyncio.utils import feed_protocol


# todo updater: 定期调用connection.check 和 connection.update,
# 把state==-1的kcptransport关闭，掉用他们的protocol.connection_lost，从kcp_transports中删除
# 一段时间没活动的connection也需要删除
class KCPUDPServerProtocol(asyncio.DatagramProtocol):
    def __init__(
        self,
        protocol_factory: Callable[[], asyncio.Protocol],
        log: Callable[[str], Any],
        pre_processor: Optional[Callable[[bytes], Tuple[int, bytes]]] = None,
        post_processor: Optional[Callable[[bytes], bytes]] = None,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ):
        self.protocol_factory = protocol_factory
        self.kcp_transports = {}  # type: Dict[int, KCPTransport]
        self._log = log
        if pre_processor is None:
            self._pre_processor = lambda data: (getconv(data), data)
        else:
            self._pre_processor = (
                pre_processor
            )  # type: Callable[[bytes], Tuple[int, bytes]]
        self._post_processor = post_processor  # type: Callable[[bytes], bytes]
        self._loop = loop or asyncio.get_running_loop()
        self._close_waiter = self._loop.create_future()
        self._drain_waiter = asyncio.Event()
        self._drain_waiter.set()
        self._update_tasks = set()  # type: Set[asyncio.Task]

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
        for kcp_transport in self.kcp_transports.values():
            kcp_transport.get_protocol().pause_writing()
        self._drain_waiter.clear()

    def resume_writing(self) -> None:
        try:
            self.transport.resume_reading()
        except AttributeError:
            pass
        for kcp_transport in self.kcp_transports.values():
            kcp_transport.get_protocol().resume_writing()
        self._drain_waiter.set()

    def datagram_received(self, data: bytes, addr):
        """Called when some datagram is received."""
        conv, data = self._pre_processor(data)
        if conv is None:
            return
        if conv not in self.kcp_transports:
            protocol = (
                self.protocol_factory()
            )  # 对于每个新虚拟连接 调用一次protocol_factory
            connection = KCPConnection(conv, partial(self._send, addr=addr), self._log)
            kcp_transport = KCPTransport(
                connection, self.transport, protocol, self._loop
            )  # 虚拟层 会调用protocol.connection_made
            self.kcp_transports[conv] = kcp_transport
            # looping update connection
            task = self._loop.create_task(self._update(kcp_transport))
            self._update_tasks.add(task)  # keep a strong ref
            task.add_done_callback(self._update_tasks.discard)
        else:
            kcp_transport = self.kcp_transports[conv]
            if kcp_transport.read_paused:
                return
            protocol = kcp_transport.get_protocol()
            connection = kcp_transport.connection
        connection.receive_data(data)
        self._loop.call_soon(feed_protocol, protocol, connection)
        # 同样call_soon，保证先connection_made再data_received，事关asyncio状态机，顺序很重要

    def error_received(self, exc):
        """Called when a send or receive operation raises an OSError.

        (Other than BlockingIOError or InterruptedError.)
        """
        for kcp_transport in self.kcp_transports.values():
            con = kcp_transport.connection
            con.log(con.logmask, f"error_received: {exc}")
        # todo should we close all virtual connections?

    async def aclose(self):
        for kcp_transport in self.kcp_transports.values():
            kcp_transport.close()
        await self.drain()
        self.transport.close()
        await self._close_waiter

    async def drain(self):
        await self._drain_waiter.wait()

    def _send(self, data: bytes, addr):
        if self._post_processor is not None:
            data = self._post_processor(data)
        self.transport.sendto(data, addr)

    async def _update(self, transport: KCPTransport):
        connection = transport.connection
        while connection.state != -1:
            now = time.perf_counter_ns() // 1000000  # ms
            connection.update(now)
            next_call = connection.check(now)
            await asyncio.sleep((next_call - now) / 1000)
        transport.get_protocol().connection_lost(None)
        del self.kcp_transports[connection.conv]

    # async def send(self, conv: int, data: bytes):
    #     kcp_transport = self.kcp_transports.get(conv, None)
    #     if kcp_transport is None:
    #         raise ValueError(f"connection {conv} not found")
    #     kcp_transport.connection.send(data)
    #     kcp_transport.connection.flush()
    #     await self.drain()


_DEFAULT_LIMIT = 2**16  # 64 KiB


async def create_kcp_server(
    loop: asyncio.AbstractEventLoop,
    protocol_factory: Callable[[], asyncio.Protocol],
    local_addr: Optional[Union[Tuple[str, int], str]],
    log: Callable[[str], Any],
    pre_processor: Optional[Callable[[bytes], Tuple[int, bytes]]] = None,
    post_processor: Optional[Callable[[bytes], bytes]] = None,
    remote_addr: Optional[Union[Tuple[str, int], str]] = None,
    *,
    family: int = 0,
    proto: int = 0,
    flags: int = 0,
    reuse_port: Optional[bool] = None,
    allow_broadcast: Optional[bool] = None,
    sock=None,
):
    return await loop.create_datagram_endpoint(
        lambda: KCPUDPServerProtocol(
            protocol_factory, log, pre_processor, post_processor, loop
        ),
        local_addr,
        remote_addr,
        family=family,
        proto=proto,
        flags=flags,
        reuse_port=reuse_port,
        allow_broadcast=allow_broadcast,
        sock=sock,
    )


async def start_kcp_server(
    client_connected_cb: Callable[
        [asyncio.StreamReader, asyncio.StreamWriter], Union[Any, Awaitable[Any]]
    ],
    local_addr: Optional[Union[Tuple[str, int], str]],
    log: Callable[[str], Any],
    pre_processor: Optional[Callable[[bytes], Tuple[int, bytes]]] = None,
    post_processor: Optional[Callable[[bytes], bytes]] = None,
    *,
    limit: int = _DEFAULT_LIMIT,
    **kwds,
):
    loop = asyncio.get_running_loop()

    def factory():
        reader = asyncio.StreamReader(limit=limit, loop=loop)
        protocol = asyncio.StreamReaderProtocol(reader, client_connected_cb, loop=loop)
        return protocol

    return await create_kcp_server(
        loop, factory, local_addr, log, pre_processor, post_processor, **kwds
    )
