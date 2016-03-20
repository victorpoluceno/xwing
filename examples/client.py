import sys
sys.path.append('.')

import time

from xwing.client import SocketClient


def main(endpoint, payload, nmessages):
    print("Starting send loop...")
    client = SocketClient(endpoint)

    start = time.time()
    for i in range(nmessages):
        client.send('0', payload)
        assert client.recv() == payload

    end = time.time()
    print(nmessages / (end - start), 'messages/sec')


if __name__ == '__main__':
    main("tcp://localhost:5555", 'x', 10000)
