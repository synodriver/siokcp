# -*- coding: utf-8 -*-
import asyncio
from typing import Any, Awaitable, Callable, Literal, Optional, Tuple, Union

from siokcp.asyncio.protocol import KCPUDPServerProtocol

_DEFAULT_LIMIT = 2**16  # 64 KiB


async def create_kcp_server(
    loop: asyncio.AbstractEventLoop,
    protocol_factory: Callable[[], asyncio.Protocol],
    local_addr: Optional[Union[Tuple[str, int], str]],
    log: Callable[[str], Any],
    pre_processor: Optional[Callable[[bytes], Tuple[int, bytes]]] = None,
    post_processor: Optional[Callable[[bytes], bytes]] = None,
    timer: Optional[Callable[[int], None]] = None,
    update_policy: Literal["normal", "lazy", "eager"] = "eager",
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
            protocol_factory,
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
