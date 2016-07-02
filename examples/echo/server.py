import asyncio
import sys
sys.path.append('.')  # NOQA

from xwing.mailbox import Node


async def echo_server(mailbox):
    while True:
        sender, message = await mailbox.recv()
        print('Echoing ...')
        await mailbox.send(sender, message)


if __name__ == '__main__':
    # python examples/echo/server.py
    loop = asyncio.get_event_loop()
    node = Node(loop)
    node.spawn(echo_server, name='echo_server')
    node.run_until_complete()
