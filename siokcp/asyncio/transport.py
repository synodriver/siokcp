# -*- coding: utf-8 -*-
import asyncio

from siokcp._kcp import KCPConnection


class KCPTransport(asyncio.transports._FlowControlMixin):
    """Virtual transport based on KCPConnection."""

    def __init__(
        self,
        connection: KCPConnection,
        transport: asyncio.DatagramTransport,
        protocol,
        loop=None,
    ):
        super().__init__(None, loop or asyncio.get_running_loop())
        self.connection = connection
        self.read_paused = False
        self._transport = transport
        self._protocol = protocol
        self._loop.call_soon(self._protocol.connection_made, self)
        # 用call_soon是防止connection_made中调用了transport.pause_reading，无论如何先把这次数据读了再说，而且transport还没准备好
        self._closing = False
        self._should_update = asyncio.Event()

    def __getattr__(self, item):
        return getattr(self._transport, item)

    def is_reading(self):
        return True

    def pause_reading(self):
        self.read_paused = True

    def resume_reading(self):
        self.read_paused = False

    def write(self, data):
        self.connection.send(data)
        self._maybe_pause_protocol()
        self._should_update.set()
        # 此处可以检查connection的阻塞状态  调用protocol.pause_writing

    def get_write_buffer_size(self):
        return self.connection.waitsnd()  # todo 是你吗

    def writelines(self, list_of_data):
        data = b"".join(list_of_data)
        self.write(data)

    def can_write_eof(self):
        return False

    def write_eof(self):
        pass

    def close(self):
        self.connection.flush()
        self._closing = True
        self.connection.state = -1

    def abort(self):
        self._closing = True
        self.connection.state = -1

    def is_closing(self):
        return self._closing

    def set_protocol(self, protocol):
        self._protocol = protocol

    def get_protocol(self):
        return self._protocol
