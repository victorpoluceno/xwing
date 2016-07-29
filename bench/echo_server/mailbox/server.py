import sys
import logging

# import asyncio
# import uvloop
# asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

from xwing.mailbox import Node

logging.basicConfig(level='INFO')
sys.path.append('.')


async def run_server(mailbox):
    while True:
        data = await mailbox.recv()
        if not data:
            break

        sender, message = data
        await mailbox.send(sender, message)


if __name__ == '__main__':
    node = Node()
    node.spawn(run_server, name='server')
    node.run()
