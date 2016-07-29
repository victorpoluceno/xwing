import sys
import asyncio
import logging

import uvloop

from xwing.socket.server import Server

logging.basicConfig(level='INFO')
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
sys.path.append('.')

async def handle_client(loop, conn):
    while True:
        data = await conn.recv()
        if not data:
            break

        await conn.send(data)

    conn.close()


async def run(loop, hub_endpoint, identity):
    server = Server(loop, hub_endpoint, identity)
    await server.listen()

    while True:
        conn = await server.accept()
        loop.create_task(handle_client(loop, conn))

    server.close()


if __name__ == '__main__':
    hub_endpoint, identity = '/var/tmp/xwing.socket', 'server0'
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run(loop, hub_endpoint, identity))
    loop.close()
