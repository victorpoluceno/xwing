import asyncio
import sys
sys.path.append('.')  # NOQA

from xwing.mailbox import Node


async def echo_client(mailbox, server):
    for i in range(100):
        await mailbox.send(server, b'x')
        _, data = await mailbox.recv()
        print('Echo received:', data)


if __name__ == '__main__':
    # python examples/echo/client.py
    loop = asyncio.get_event_loop()
    node = Node(loop)
    node.spawn(echo_client, 'echo_server')
    node.run_until_complete()
