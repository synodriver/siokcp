<h1 align="center"><i>✨ siokcp ✨ </i></h1>

<h3 align="center">The python binding for <a href="https://github.com/skywind3000/kcp">kcp</a> </h3>



[![pypi](https://img.shields.io/pypi/v/siokcp.svg)](https://pypi.org/project/siokcp/)
![python](https://img.shields.io/pypi/pyversions/siokcp)
![implementation](https://img.shields.io/pypi/implementation/siokcp)
![wheel](https://img.shields.io/pypi/wheel/siokcp)
![license](https://img.shields.io/github/license/synodriver/siokcp.svg)
![action](https://img.shields.io/github/workflow/status/synodriver/siokcp/build%20wheel)


# Usage 
```
from siokcp import KCPConnection

con = KCPConnection(1, send_callback, log_callback)
con.receive_data(somedata)
p = con.next_event()

```

```python
import asyncio
from siokcp.asyncio import start_kcp_server, open_kcp_connection

async def serve(event):
    async def cb(reader: asyncio.StreamReader, writer):
        data = await reader.read(1024)
        writer.write(data)
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    tr, pro = await start_kcp_server(cb, ("0.0.0.0", 11000), print)
    await event.wait()
    tr.close()
    
async def main():
    ev = asyncio.Event()
    ev.clear()
    asyncio.create_task(serve(ev))
    r, w = await open_kcp_connection(("127.0.0.1", 11000), 10, print)
    w.write(b"Hello, world!")
    await w.drain()
    print(await r.read(100))
    ev.set()

asyncio.run(main())
```


# Public functions
```python
from typing import  Optional

IKCP_LOG_INPUT: int
IKCP_LOG_IN_ACK: int
IKCP_LOG_IN_DATA: int
IKCP_LOG_IN_PROBE: int
IKCP_LOG_IN_WINS: int
IKCP_LOG_OUTPUT: int
IKCP_LOG_OUT_ACK: int
IKCP_LOG_OUT_DATA: int
IKCP_LOG_OUT_PROBE: int
IKCP_LOG_OUT_WINS: int
IKCP_LOG_RECV: int
IKCP_LOG_SEND: int


def get_conv(data: bytes) -> int: ...

class KCPConnection:
    conv: int
    current: int
    cwnd: int
    dead_link: int
    fastlimit: int
    fastresend: int
    incr: int
    interval: int
    logmask: int
    mss: int
    mtu: int
    nocwnd: int
    nodelay_: int
    nrcv_buf: int
    nrcv_que: int
    nsnd_buf: int
    nsnd_que: int
    probe: int
    probe_wait: int
    rcv_nxt: int
    rcv_wnd: int
    rmt_wnd: int
    rx_minrto: int
    rx_rto: int
    rx_rttval: int
    rx_srtt: int
    send_cb: object
    snd_nxt: int
    snd_una: int
    snd_wnd: int
    ssthresh: int
    state: int
    stream: int
    ts_flush: int
    ts_lastack: int
    ts_probe: int
    ts_recent: int
    updated: int
    xmit: int
    @classmethod
    def __init__(cls, conv: int, send_cb: object, log_cb: object) -> None: ...
    def check(self, current: int) -> int: ...
    def flush(self) -> None: ...
    def log(self, mask: int, data: str) -> None: ...
    def next_event(self) -> Optional[bytes]: ...
    def next_event_into(self, buffer: bytearray) -> int: ...
    def nodelay(self, nodelay: int, interval: int, resend: int, nc: int) -> int: ...
    def peeksize(self) -> int: ...
    def receive_data(self, data: bytes) -> int: ...
    def send(self, data: bytes) -> int: ...
    def setmtu(self, mtu: int) -> int: ...
    def update(self, current: int) -> int: ...
    def waitsnd(self) -> int: ...
    def wndsize(self, sndwnd: int, rcvwnd: int) -> int: ...
```
### siokcp.asyncio
```python
from typing import Callable, Awaitable, Any, Literal
from socket import socket
import asyncio

async def create_kcp_connection(
    loop: asyncio.AbstractEventLoop,
    protocol_factory: Callable[[], asyncio.Protocol],
    conv: int,
    remote_addr: tuple[str, int] | str | None,
    log: Callable[[str], Any],
    pre_processor: Callable[[bytes], tuple[int, bytes]] | None = None,
    post_processor: Callable[[bytes], bytes] | None = None,
    timer: Callable[[], None] | None = None,
    update_policy: Literal["normal", "lazy", "eager"] = "eager",
    local_addr: tuple[str, int] | str | None = None,
    *,
    family: int = 0,
    proto: int = 0,
    flags: int = 0,
    reuse_port: bool | None = None,
    allow_broadcast: bool | None = None,
    sock: socket | None = None
): ...
async def open_kcp_connection(
    remote_addr: tuple[str, int] | str | None,
    conv: int,
    log: Callable[[str], Any],
    pre_processor: Callable[[bytes], tuple[int, bytes]] | None = None,
    post_processor: Callable[[bytes], bytes] | None = None,
    *,
    limit=...,
    **kwds
): ...
async def create_kcp_server(
    loop: asyncio.AbstractEventLoop,
    protocol_factory: Callable[[], asyncio.Protocol],
    local_addr: tuple[str, int] | str | None,
    log: Callable[[str], Any],
    pre_processor: Callable[[bytes], tuple[int, bytes]] | None = None,
    post_processor: Callable[[bytes], bytes] | None = None,
    timer: Callable[[int], None] | None = None,
    update_policy: Literal["normal", "lazy", "eager"] = "eager",
    remote_addr: tuple[str, int] | str | None = None,
    *,
    family: int = 0,
    proto: int = 0,
    flags: int = 0,
    reuse_port: bool | None = None,
    allow_broadcast: bool | None = None,
    sock: socket | None = None
): ...
async def start_kcp_server(
    client_connected_cb: Callable[
        [asyncio.StreamReader, asyncio.StreamWriter], Any | Awaitable[Any]
    ],
    local_addr: tuple[str, int] | str | None,
    log: Callable[[str], Any],
    pre_processor: Callable[[bytes], tuple[int, bytes]] | None = None,
    post_processor: Callable[[bytes], bytes] | None = None,
    *,
    limit: int = ...,
    **kwds
): ...

```