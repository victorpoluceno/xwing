import asyncio
import sys
sys.path.append('.')  # NOQA

from examples.actor.model import Node


async def pong_actor(mailbox):
    sender, message = await mailbox.recv()
    await mailbox.send(sender, 'pong')


async def ping_actor(mailbox, pong_id):
    await mailbox.send(pong_id, 'ping')
    print('Got: ', await mailbox.recv())


if __name__ == '__main__':
    # python examples/actor/server.py
    hub_frontend, hub_backend = '127.0.0.1:5555', '/var/tmp/xwing.socket'
    loop = asyncio.get_event_loop()
    loop.set_debug(1)

    # Start a actor node by which we can spawn actors
    node = Node(loop, hub_frontend, hub_backend)

    # Spawn an pong actor and get its id
    pong_id = node.spawn(pong_actor)
    node.spawn(ping_actor, pong_id)

    loop.run_until_complete(node.run())
    loop.close()
