import sys
sys.path.append('.')
import asyncio

from xwing.socket.server import Server


async def run(loop, hub_endpoint, identity):
    socket_server = Server(loop, hub_endpoint, identity)
    await socket_server.listen()
    conn = await socket_server.accept()

    while True:
        data = await conn.recv()
        if not data:
            break

        print('Echoing ...')
        await conn.send(data)


if __name__ == '__main__':
    # python examples/socket/echo/server.py /var/tmp/xwing.socket server0
    print(sys.argv)
    hub_endpoint, identity = sys.argv[1:]
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run(loop, hub_endpoint, identity))
    loop.close()
