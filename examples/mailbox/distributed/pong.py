import sys
sys.path.append('.')  # NOQA

from xwing.mailbox import initialize, spawn, run
initialize()


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
    # python examples/mailbox/distributed/pong.py
    spawn(pong, name='pong')
    run()
