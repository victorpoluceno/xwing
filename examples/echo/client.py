import sys
sys.path.append('.')
import asyncio
import time

from xwing.socket.client import Client


async def main(loop, endpoint):
    client = Client(loop, endpoint)
    conn = client.connect('server0')

    for i in range(100):
        await conn.send(b'x')
        print('Echo received: %r' % await conn.recv())


if __name__ == '__main__':
    # python examples/echo/client.py
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop, "localhost:5555"))
    loop.close()
