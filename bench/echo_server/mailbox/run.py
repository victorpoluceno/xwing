import time
import logging
from concurrent import futures

from xwing.mailbox import initialize, spawn, run, get_node_instance
initialize()

logging.basicConfig(level='INFO')


async def send(mailbox, start, duration, payload, target_pid):
    n = 0
    while time.monotonic() - start < duration:
        await mailbox.send(target_pid, mailbox.pid, payload)
        await mailbox.recv()
        n += 1

    await mailbox.send('collector', n)


def run_bench(start, duration, data=b'x'):
    initialize()  # initialize a new node with a new event loop
    spawn(send, start, duration, b'x', 'server')
    run()


async def collector(mailbox, wait_for):
    total = 0
    for i in range(wait_for):
        r = await mailbox.recv()
        total += r[0]

    print('Requests per second w=%d' % wait_for, total)


async def dispatch(loop, executor, start, duration):
    await loop.run_in_executor(executor, run_bench, start, duration)


def main(number_of_workers=4, duration=30):
    start = time.monotonic()
    spawn(collector, number_of_workers, name='collector')
    executor = futures.ProcessPoolExecutor(max_workers=number_of_workers)
    for i in range(number_of_workers):
        node = get_node_instance()
        node.loop.create_task(dispatch(node.loop, executor, start, duration))

    run()


if __name__ == '__main__':
    main(number_of_workers=4)
