from xwing.mailbox import init_node, start_node, spawn


async def pong(mailbox):
    while True:
        data = await mailbox.recv()
        if len(data) == 1 and data[0] == 'finished':
            print('Pong finished')
            break

        print('Pong received ping')
        message, pid = data
        await mailbox.send(pid, 'pong')


async def ping(mailbox, n):
    for _ in range(n):
        await mailbox.send('pong', 'ping', mailbox.pid)
        message = await mailbox.recv()
        if message[0] == 'pong':
            print('Ping received pong')

    await mailbox.send('pong', 'finished')


if __name__ == '__main__':
    # python examples/mailbox/ping_pong.py
    init_node()
    spawn(pong, name='pong')
    spawn(ping, 3)
    start_node()
