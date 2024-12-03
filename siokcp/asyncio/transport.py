# -*- coding: utf-8 -*-
import asyncio

from siokcp._kcp import KCPConnection


class KCPTransport(asyncio.Transport):
    """Virtual transport based on KCPConnection."""

    def __init__(
        self,
        connection: KCPConnection,
        transport: asyncio.DatagramTransport,
        protocol,
        loop=None,
    ):
        self.connection = connection
        self.read_paused = False
        self._transport = transport
        self._loop = loop or asyncio.get_running_loop()
        self._protocol = protocol
        self._loop.call_soon(self._protocol.connection_made, self)
        # 用call_soon是防止connection_made中调用了transport.pause_reading，无论如何先把这次数据读了再说
        self._closing = False

    def __getattr__(self, item):
        return getattr(self._transport, item)

    def is_reading(self):
        return True

    def pause_reading(self):
        self.read_paused = True

    def resume_reading(self):
        self.read_paused = False

    def set_write_buffer_limits(self, high=None, low=None):
        pass  # todo self.connection.wndsize

    def get_write_buffer_size(self):
        return 0  # todo self.connection.wndsize

    def write(self, data):
        self.connection.send(data)
        self.connection.flush()

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
