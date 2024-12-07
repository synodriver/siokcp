# -*- coding: utf-8 -*-
import asyncio
import time
from functools import partial
from typing import Any, Callable, Dict, Optional, Set, Tuple

from siokcp._kcp import KCPConnection, getconv
from siokcp.asyncio.transport import KCPTransport
from siokcp.asyncio.utils import feed_protocol


# todo 一段时间没活动的connection也需要删除 吗？
class BaseKCPProtocol(asyncio.DatagramProtocol):
    def __init__(
        self,
        protocol_factory: Callable[[], asyncio.Protocol],
        log: Callable[[str], Any],
        pre_processor: Optional[Callable[[bytes], Tuple[int, bytes]]] = None,
        post_processor: Optional[Callable[[bytes], bytes]] = None,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ):
        self.protocol_factory = protocol_factory
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

    def connection_made(self, transport: asyncio.DatagramTransport) -> None:
        self.transport = transport

    async def aclose(self):
        await self.drain()
        self.transport.close()
        await self._close_waiter

    async def drain(self):
        await self._drain_waiter.wait()

    def _send(self, data: bytes, addr=None):
        if self._post_processor is not None:
            data = self._post_processor(data)
        self.transport.sendto(data, addr)
        return 0  # make lib kcp happy

    # async def send(self, conv: int, data: bytes):
    #     kcp_transport = self.kcp_transports.get(conv, None)
    #     if kcp_transport is None:
    #         raise ValueError(f"connection {conv} not found")
    #     kcp_transport.connection.send(data)
    #     kcp_transport.connection.flush()
    #     await self.drain()


class KCPUDPServerProtocol(BaseKCPProtocol):
    def __init__(
        self,
        protocol_factory: Callable[[], asyncio.Protocol],
        log: Callable[[str], Any],
        pre_processor: Optional[Callable[[bytes], Tuple[int, bytes]]] = None,
        post_processor: Optional[Callable[[bytes], bytes]] = None,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ):
        super().__init__(protocol_factory, log, pre_processor, post_processor, loop)
        self.kcp_transports = {}  # type: Dict[int, KCPTransport]
        self._update_tasks = set()  # type: Set[asyncio.Task]

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
            protocol = kcp_transport.get_protocol()
            try:
                protocol.pause_writing()
            except (SystemExit, KeyboardInterrupt):
                raise
            except BaseException as exc:
                self._loop.call_exception_handler(
                    {
                        "message": "protocol.pause_writing() failed",
                        "exception": exc,
                        "transport": kcp_transport,
                        "protocol": protocol,
                    }
                )
        self._drain_waiter.clear()

    def resume_writing(self) -> None:
        try:
            self.transport.resume_reading()
        except AttributeError:
            pass
        for kcp_transport in self.kcp_transports.values():
            protocol = kcp_transport.get_protocol()
            try:
                protocol.resume_writing()
            except (SystemExit, KeyboardInterrupt):
                raise
            except BaseException as exc:
                self._loop.call_exception_handler(
                    {
                        "message": "protocol.resume_writing() failed",
                        "exception": exc,
                        "transport": kcp_transport,
                        "protocol": protocol,
                    }
                )
        self._drain_waiter.set()

    def datagram_received(self, data: bytes, addr):
        """Called when some datagram is received."""
        conv, data = self._pre_processor(data)
        # print(f"conv: {conv}, data: {data}")
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
            kcp_transport._extra["peername"] = (
                addr  # 定义了remote_addr才会有这个，服务端显然没有，这里强行塞进去
            )
            self.kcp_transports[conv] = kcp_transport
            # looping update connection
            task = self._loop.create_task(self._update(kcp_transport))
            self._update_tasks.add(task)  # keep a strong ref
            task.add_done_callback(self._update_tasks.discard)
        else:
            # print("transport exists")
            kcp_transport = self.kcp_transports[conv]
            protocol = kcp_transport.get_protocol()
            connection = kcp_transport.connection
            if addr != kcp_transport.get_extra_info("peername"):  # keep alive
                # print("change ip")
                kcp_transport._extra["peername"] = (
                    addr  # client ip变化，但是conv不变，视为同一连接
                )
                connection.send_cb = partial(self._send, addr=addr)  # 发送地址得改改
        if kcp_transport.read_paused:
            return
        # print("receive_data")
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
        for task in self._update_tasks:
            try:
                await task
            except asyncio.CancelledError:
                pass
        await super().aclose()

    async def _update(self, transport: KCPTransport):
        connection = transport.connection
        try:
            while connection.state != -1:
                now = time.perf_counter_ns() // 1000000  # ms
                connection.update(
                    now
                )  # 此处可以检查connection的阻塞状态  调用protocol.resume_writing
                transport._maybe_resume_protocol()
                next_call = connection.check(now)
                # print("next_call", next_call)
                await asyncio.sleep((next_call - now) / 1000)
        finally:
            # print(f"close connection {connection.conv} in _update")
            transport.get_protocol().connection_lost(None)
            del self.kcp_transports[connection.conv]


class KCPUDPClientProtocol(BaseKCPProtocol):
    """与server不一样，client只有一个KCPConnection"""

    def __init__(
        self,
        protocol_factory: Callable[[], asyncio.Protocol],
        conv: int,
        log: Callable[[str], Any],
        pre_processor: Optional[Callable[[bytes], Tuple[int, bytes]]] = None,
        post_processor: Optional[Callable[[bytes], bytes]] = None,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ):
        super().__init__(protocol_factory, log, pre_processor, post_processor, loop)
        self.conv = conv
        self.kcp_transport = None  # type: KCPTransport
        self._update_task = None

    def connection_made(self, transport: asyncio.DatagramTransport) -> None:
        super().connection_made(transport)
        protocol = (
            self.protocol_factory()
        )  # 对于每个新虚拟连接 调用一次protocol_factory
        self.kcp_transport = KCPTransport(
            KCPConnection(self.conv, self._send, self._log),
            transport,
            protocol,
            self._loop,
        )
        self._update_task = self._loop.create_task(self._update())
        # def cb(f):
        #     self._update_task = None
        # task.add_done_callback(cb)

    def connection_lost(self, exc: Optional[Exception]) -> None:
        self.transport = None
        if self.kcp_transport is not None:
            self.kcp_transport.get_protocol().connection_lost(exc)
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
        protocol = self.kcp_transport.get_protocol()
        try:
            protocol.pause_writing()
        except (SystemExit, KeyboardInterrupt):
            raise
        except BaseException as exc:
            self._loop.call_exception_handler(
                {
                    "message": "protocol.pause_writing() failed",
                    "exception": exc,
                    "transport": self.kcp_transport,
                    "protocol": protocol,
                }
            )
        self._drain_waiter.clear()

    def resume_writing(self) -> None:
        try:
            self.transport.resume_reading()
        except AttributeError:
            pass
        protocol = self.kcp_transport.get_protocol()
        try:
            protocol.resume_writing()
        except (SystemExit, KeyboardInterrupt):
            raise
        except BaseException as exc:
            self._loop.call_exception_handler(
                {
                    "message": "protocol.resume_writing() failed",
                    "exception": exc,
                    "transport": self.kcp_transport,
                    "protocol": protocol,
                }
            )
        self._drain_waiter.set()

    def datagram_received(self, data: bytes, addr):
        """Called when some datagram is received."""
        conv, data = self._pre_processor(data)
        if conv != self.conv:
            return
        if self.kcp_transport.read_paused:
            return
        self.kcp_transport.connection.receive_data(data)
        self._loop.call_soon(
            feed_protocol,
            self.kcp_transport.get_protocol(),
            self.kcp_transport.connection,
        )

    async def _update(self):
        connection = self.kcp_transport.connection
        try:
            while connection.state != -1:
                now = time.perf_counter_ns() // 1000000  # ms
                connection.update(
                    now
                )  # 此处可以检查connection的阻塞状态  调用protocol.resume_writing
                self.kcp_transport._maybe_resume_protocol()
                next_call = connection.check(now)
                await asyncio.sleep((next_call - now) / 1000)
        finally:
            self.kcp_transport.get_protocol().connection_lost(None)
            self.kcp_transport = None

    async def aclose(self):
        self.kcp_transport.close()
        try:
            await self._update_task
        except asyncio.CancelledError:
            pass
        self._update_task = None
        await super().aclose()
