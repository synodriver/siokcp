# -*- coding: utf-8 -*-
import asyncio

from siokcp._kcp import KCPConnection


def feed_protocol(protocol: asyncio.BaseProtocol, connection: KCPConnection):
    if not isinstance(protocol, asyncio.BufferedProtocol):
        packet: bytes = connection.next_event()
        protocol.data_received(packet)
    else:
        size = connection.peeksize()
        buf = protocol.get_buffer(size)
        hr = connection.next_event_into(buf)
        protocol.buffer_updated(hr)
