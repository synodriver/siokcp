# -*- coding: utf-8 -*-
import asyncio
from typing import Any, Callable, Literal, Optional, Tuple, Union

from siokcp.asyncio.protocol import KCPUDPClientProtocol


async def create_kcp_connection(
    loop: asyncio.AbstractEventLoop,
    protocol_factory: Callable[[], asyncio.Protocol],
    conv: int,
    remote_addr: Optional[Union[Tuple[str, int], str]],
    log: Callable[[str], Any],
    pre_processor: Optional[Callable[[bytes], Tuple[int, bytes]]] = None,
    post_processor: Optional[Callable[[bytes], bytes]] = None,
    timer: Optional[Callable[[], None]] = None,
    update_policy: Literal["normal", "lazy", "eager"] = "eager",
    local_addr: Optional[Union[Tuple[str, int], str]] = None,
    *,
    family: int = 0,
    proto: int = 0,
    flags: int = 0,
    reuse_port: Optional[bool] = None,
    allow_broadcast: Optional[bool] = None,
    sock=None,
):
    _, udp_protocol = await loop.create_datagram_endpoint(
        lambda: KCPUDPClientProtocol(
            protocol_factory,
            conv,
            log,
            pre_processor,
            post_processor,
            timer,
            update_policy,
            loop,
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
    return udp_protocol.kcp_transport, udp_protocol.kcp_transport.get_protocol()


_DEFAULT_LIMIT = 2**16  # 64 KiB


async def open_kcp_connection(
    remote_addr: Optional[Union[Tuple[str, int], str]],
    conv: int,
    log: Callable[[str], Any],
    pre_processor: Optional[Callable[[bytes], Tuple[int, bytes]]] = None,
    post_processor: Optional[Callable[[bytes], bytes]] = None,
    *,
    limit=_DEFAULT_LIMIT,
    **kwds,
):
    loop = asyncio.get_running_loop()
    reader = asyncio.StreamReader(limit=limit, loop=loop)
    protocol = asyncio.StreamReaderProtocol(reader, loop=loop)
    transport, _ = await create_kcp_connection(
        loop,
        lambda: protocol,
        conv,
        remote_addr,
        log,
        pre_processor,
        post_processor,
        **kwds,
    )
    writer = asyncio.StreamWriter(transport, protocol, reader, loop)
    return reader, writer
