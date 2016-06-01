import asyncio

from xwing.socket.server import Server

BACKEND_ADDRESS = '/var/tmp/xwing.socket'



async def start_server(loop):
    server = Server(loop, BACKEND_ADDRESS, 'server0')
    await server.listen()

    conn = await server.accept()
    while True:
        data = await conn.recv()
        if not data:
            break

        await conn.send(data)

    conn.close()


loop = asyncio.get_event_loop()
loop.run_until_complete(start_server(loop))
loop.close()