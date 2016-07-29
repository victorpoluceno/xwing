import time
from concurrent import futures

# import asyncio
# import uvloop
# asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

from xwing.mailbox import Node


async def send(mailbox, start, duration, payload, target_pid):
    n = 0
    while time.monotonic() - start < duration:
        await mailbox.send(target_pid, mailbox.pid, payload)
        await mailbox.recv()
        n += 1

    await mailbox.send('collector', n)


def run_bench(start, duration, data=b'x'):
    node = Node(new_loop=True)
    node.spawn(send, start, duration, b'x', 'server')
    node.run()


def main(number_of_workers=4, duration=30):
    start = time.monotonic()

    async def collector(mailbox, wait_for):
        total = 0
        for i in range(wait_for):
            r = await mailbox.recv()
            total += r[0]

        print('Requests per second w=%d' % wait_for, total)

    async def dispatch(loop, executor):
        await loop.run_in_executor(executor, run_bench, start, duration)

    node = Node()
    node.spawn(collector, number_of_workers, name='collector')

    executor = futures.ProcessPoolExecutor(max_workers=number_of_workers)
    for i in range(number_of_workers):
        node.loop.create_task(dispatch(node.loop, executor))

    node.run()


if __name__ == '__main__':
    main(number_of_workers=4)
