from xwing.mailbox import initialize, spawn, start
initialize()


async def ping(mailbox, n, pong_node):
    for _ in range(n):
        await mailbox.send(pong_node, 'ping', mailbox.pid)
        message = await mailbox.recv()
        if message[0] == 'pong':
            print('Ping received pong')

    await mailbox.send('pong', 'finished')


if __name__ == '__main__':
    # python examples/mailbox/distributed/ping.py
    spawn(ping, 3, 'pong@127.0.0.1')
    start()
