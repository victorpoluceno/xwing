import sys
sys.path.append('.')

import asyncio
import time
import subprocess
import logging
logging.basicConfig(level=logging.DEBUG)

import pytest

from xwing.socket.client import Client


FRONTEND_ADDRESS = '127.0.0.1:5555'


def setup_module(module):
    module.hub_process = subprocess.Popen('bin/xwing'); time.sleep(1)
    module.server_process = subprocess.Popen(['python', 'tests/run_server.py'])
    
def teardown_module(module):
    module.hub_process.kill()
    module.server_process.kill()


class TestIntegration:

    @classmethod
    def setup_class(cls):
        loop = asyncio.get_event_loop()
        client = Client(loop, FRONTEND_ADDRESS)

        async def connect(cls):
            while True:
                try:
                    cls.connection = await client.connect('server0')
                except ConnectionError:
                    await asyncio.sleep(1)
                    continue
                else:
                    break

        loop.run_until_complete(asyncio.wait_for(connect(cls), 30))

    @classmethod
    def teardown_class(cls):
        cls.connection.close()

    @pytest.mark.asyncio
    async def test_auto_identity(self):
        assert self.client.identity

    @pytest.mark.asyncio
    async def test_send_and_recv_str(self):
        data = 'ping'
        await self.connection.send_str(data)
        assert await self.connection.recv_str() == data

    @pytest.mark.asyncio
    async def test_send_and_recv(self):
        data = b'ping'
        await self.connection.send(data)
        assert await self.connection.recv() == data
