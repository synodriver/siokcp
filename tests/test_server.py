# -*- coding: utf-8 -*-
import asyncio
import sys

sys.path.append(".")
from unittest import IsolatedAsyncioTestCase

from siokcp import getconv
from siokcp.asyncio import create_kcp_server, open_kcp_connection, start_kcp_server


class TestServer(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        pass

    async def asyncTearDown(self):
        pass

    async def test_server(self):
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

        ev = asyncio.Event()
        ev.clear()
        asyncio.create_task(serve(ev))
        r, w = await open_kcp_connection(("127.0.0.1", 11000), 10, print)
        w.write(b"Hello, world!")
        await w.drain()
        self.assertEqual(await r.read(100), b"Hello, world!")
        w.write(b"GuGu")
        await w.drain()
        with self.assertRaises(asyncio.TimeoutError):
            await asyncio.wait_for(r.read(100), 2)
            # 为什么超时？因为服务器关闭了连接，但是client没有，第二次发送数据的时候,服务器的sn从0开始计算
            # 但是client的sn延续上次的sn，所以服务器会认为0号包丢了，就一直等
        ev.set()

    async def test_server2(self):
        async def serve(event):
            async def cb(reader: asyncio.StreamReader, writer):
                data = await reader.read(1024)
                writer.write(data)
                await writer.drain()

            tr, pro = await start_kcp_server(cb, ("0.0.0.0", 11000), print)
            await event.wait()
            tr.close()

        ev = asyncio.Event()
        ev.clear()
        asyncio.create_task(serve(ev))
        r, w = await open_kcp_connection(("127.0.0.1", 11000), 10, print)
        w.write(b"Hello, world!")
        await w.drain()
        self.assertEqual(await r.read(100), b"Hello, world!")
        w.write(b"GuGu")
        await w.drain()
        with self.assertRaises(asyncio.TimeoutError):
            await asyncio.wait_for(r.read(100), 2)
            # 为什么还是超时？StreamWriter在__del__的时候会调用transport.close，第二次发送数据的时候，服务器又是个新transport，sn从0开始计算
            # 但是client的sn延续上次的sn，所以服务器会认为0号包丢了，就一直等
        ev.set()

    async def test_server3(self):
        async def serve(event):
            async def cb(reader: asyncio.StreamReader, writer):
                while True:
                    data = await reader.read(1024)
                    writer.write(data)
                    await writer.drain()

            tr, pro = await start_kcp_server(cb, ("0.0.0.0", 11000), print)
            await event.wait()
            tr.close()

        ev = asyncio.Event()
        ev.clear()
        asyncio.create_task(serve(ev))
        r, w = await open_kcp_connection(("127.0.0.1", 11000), 10, print)
        w.write(b"Hello, world!")
        await w.drain()
        self.assertEqual(await r.read(100), b"Hello, world!")
        w.write(b"GuGu")
        await w.drain()
        self.assertEqual(await r.read(100), b"GuGu")
        ev.set()

    async def test_server3_lazy(self):
        async def serve(event):
            async def cb(reader: asyncio.StreamReader, writer):
                while True:
                    data = await reader.read(1024)
                    writer.write(data)
                    await writer.drain()

            tr, pro = await start_kcp_server(
                cb, ("0.0.0.0", 11000), print, update_policy="lazy"
            )
            await event.wait()
            tr.close()

        ev = asyncio.Event()
        ev.clear()
        asyncio.create_task(serve(ev))
        r, w = await open_kcp_connection(
            ("127.0.0.1", 11000), 10, print, update_policy="lazy"
        )
        w.write(b"Hello, world!")
        await w.drain()
        self.assertEqual(await r.read(100), b"Hello, world!")
        w.write(b"GuGu")
        await w.drain()
        self.assertEqual(await r.read(100), b"GuGu")
        ev.set()

    async def test_server3_normal(self):
        async def serve(event):
            async def cb(reader: asyncio.StreamReader, writer):
                while True:
                    data = await reader.read(1024)
                    writer.write(data)
                    await writer.drain()

            tr, pro = await start_kcp_server(
                cb, ("0.0.0.0", 11000), print, update_policy="normal"
            )
            await event.wait()
            tr.close()

        ev = asyncio.Event()
        ev.clear()
        asyncio.create_task(serve(ev))
        r, w = await open_kcp_connection(
            ("127.0.0.1", 11000), 10, print, update_policy="normal"
        )
        w.write(b"Hello, world!")
        await w.drain()
        self.assertEqual(await r.read(100), b"Hello, world!")
        w.write(b"GuGu")
        await w.drain()
        self.assertEqual(await r.read(100), b"GuGu")
        ev.set()

    async def test_server3_normal_wait(self):
        async def serve(event):
            async def cb(reader: asyncio.StreamReader, writer):
                while True:
                    data = await reader.read(1024)
                    writer.write(data)
                    await writer.drain()

            tr, pro = await start_kcp_server(
                cb, ("0.0.0.0", 11000), print, update_policy="normal"
            )
            await event.wait()
            tr.close()

        ev = asyncio.Event()
        ev.clear()
        asyncio.create_task(serve(ev))
        r, w = await open_kcp_connection(
            ("127.0.0.1", 11000), 10, print, update_policy="normal"
        )
        w.write(b"Hello, world!")
        await w.drain()
        self.assertEqual(await r.read(100), b"Hello, world!")
        await asyncio.sleep(0.5)
        w.write(b"GuGu")
        await w.drain()
        self.assertEqual(await r.read(100), b"GuGu")
        ev.set()
        w.close()
        await w.wait_closed()

    async def test_protocol_server(self):
        class EchoProtocol(asyncio.Protocol):
            def connection_made(self, transport):
                self.transport = transport

            def data_received(self, data):
                self.transport.write(data)

        async def serve(event):
            tr, pro = await create_kcp_server(
                asyncio.get_running_loop(), EchoProtocol, ("0.0.0.0", 11000), print
            )
            await event.wait()
            tr.close()

        ev = asyncio.Event()
        ev.clear()
        asyncio.create_task(serve(ev))
        r, w = await open_kcp_connection(("127.0.0.1", 11000), 10, print)
        w.write(b"Hello, world!")
        await w.drain()
        self.assertEqual(await r.read(100), b"Hello, world!")
        w.write(b"GuGu")
        await w.drain()
        self.assertEqual(await r.read(100), b"GuGu")
        ev.set()

    async def test_buffer_protocol_server(self):

        class EchoProtocol(asyncio.BufferedProtocol):
            def __init__(self):
                self._buffer = bytearray(10)

            def connection_made(self, transport):
                self.transport = transport

            def connection_lost(self, exc):
                self.transport = None

            def get_buffer(self, sizehint):
                if s := sizehint - len(self._buffer) > 0:
                    self._buffer.extend(bytes(s))
                return self._buffer

            def buffer_updated(self, nbytes):
                self.transport.write(self._buffer[:nbytes])

        async def serve(event):
            tr, pro = await create_kcp_server(
                asyncio.get_running_loop(), EchoProtocol, ("0.0.0.0", 11000), print
            )
            await event.wait()
            tr.close()

        ev = asyncio.Event()
        ev.clear()
        asyncio.create_task(serve(ev))
        r, w = await open_kcp_connection(("127.0.0.1", 11000), 10, print)
        w.write(b"Hello, world!")
        await w.drain()
        self.assertEqual(await r.read(100), b"Hello, world!")
        w.write(b"GuGu")
        await w.drain()
        self.assertEqual(await r.read(100), b"GuGu")
        ev.set()

    async def test_pre_post_processor(self):
        import ftea

        class Crypto:
            def __init__(self):
                self.tea = ftea.TEA(b"1234567812345678")

            def pre_processor(self, data):
                data = self.tea.decrypt_qq(data)
                return (
                    getconv(data),
                    data,
                )

            def post_processor(self, data):
                return self.tea.encrypt_qq(data)

        crypto = Crypto()

        async def serve(event):
            async def cb(reader: asyncio.StreamReader, writer):
                data = await reader.read(1024)
                writer.write(data)
                await writer.drain()

            tr, pro = await start_kcp_server(
                cb,
                ("0.0.0.0", 11000),
                print,
                crypto.pre_processor,
                crypto.post_processor,
            )
            await event.wait()
            tr.close()

        ev = asyncio.Event()
        ev.clear()
        asyncio.create_task(serve(ev))
        r, w = await open_kcp_connection(
            ("127.0.0.1", 11000), 10, print, crypto.pre_processor, crypto.post_processor
        )
        w.write(b"Hello, world!")
        await w.drain()
        self.assertEqual(await r.read(100), b"Hello, world!")
        w.write(b"GuGu")
        await w.drain()
        with self.assertRaises(asyncio.TimeoutError):
            await asyncio.wait_for(r.read(100), 2)
            # 为什么还是超时？StreamWriter在__del__的时候会调用transport.close，第二次发送数据的时候，服务器又是个新transport，sn从0开始计算
            # 但是client的sn延续上次的sn，所以服务器会认为0号包丢了，就一直等
        ev.set()


if __name__ == "__main__":
    import unittest

    unittest.main()
