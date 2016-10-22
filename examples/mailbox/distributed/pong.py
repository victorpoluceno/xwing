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


if __name__ == '__main__':
    init_node()
    spawn(pong, name='pong')
    start_node()
