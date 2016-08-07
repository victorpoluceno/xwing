import time
import asyncio
import logging
from concurrent import futures

from xwing.socket.client import Client

logging.basicConfig(level='INFO')


async def connect_and_send(loop, endpoint, payload, start, duration):
    client = Client(loop, endpoint)
    conn = await client.connect('server0')

    n = 0
    while time.monotonic() - start < duration:
        await conn.send(payload)
        await conn.recv()
        n += 1

    return n


def run(start, duration, data=b'x'):
    loop = asyncio.get_event_loop()
    requests = loop.run_until_complete(connect_and_send(
        loop, "localhost:5555", b'x', start, duration))
    loop.close()
    return requests


def main(number_of_workers=10, duration=30):
    start = time.monotonic()
    with futures.ProcessPoolExecutor(max_workers=number_of_workers) as \
            executor:
        fs = [executor.submit(run, start, duration) for i in range(number_of_workers)]
        reqs_per_second = sum([f.result() for f in futures.wait(fs).done]) / duration
        print('Requests per second w=%d: ' % number_of_workers,
              reqs_per_second)


if __name__ == '__main__':
    main(number_of_workers=4)
