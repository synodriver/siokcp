# -*- coding: utf-8 -*-
import asyncio

from siokcp._kcp import KCPConnection


def feed_protocol(protocol: asyncio.BaseProtocol, connection: KCPConnection):
    if not isinstance(protocol, asyncio.BufferedProtocol):
        packet: bytes = connection.next_event()
        if packet is None:  # EAGAIN
            return
        protocol.data_received(packet)
    else:
        size = connection.peeksize()
        buf = protocol.get_buffer(size)
        hr = connection.next_event_into(buf)
        if hr < 0:
            hr = 0  # EAGAIN
        protocol.buffer_updated(hr)
