import logging

from xwing.node import initialize, spawn, start
initialize()

logging.basicConfig(level='INFO')


async def run_server(mailbox):
    while True:
        data = await mailbox.recv()
        if not data:
            break

        sender, message = data
        await mailbox.send(sender, message)


if __name__ == '__main__':
    spawn(run_server, name='server')
    start()
