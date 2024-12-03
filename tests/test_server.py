# -*- coding: utf-8 -*-
from unittest import IsolatedAsyncioTestCase

from loguru import logger

from siokcp.asyncio import create_kcp_server, start_kcp_server


class TestServer(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        pass

    async def asyncTearDown(self):
        pass

    async def test_server(self):
        async def cb(reader, writer):
            data = await reader.read(1024)
            writer.write(data)
            await writer.drain()

        tr, pro = await start_kcp_server(cb, ("0.0.0.0", 8000), logger.info)
        print(f"serving {tr} {pro}")


if __name__ == "__main__":
    import unittest

    unittest.main()
