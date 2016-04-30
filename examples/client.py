import sys
sys.path.append('.')

import time

from xwing.socket.client import SocketClient

# python examples/client.py


def main(endpoint, payload, nmessages):
    print("Starting send loop...")
    client = SocketClient(endpoint)
    client.connect('0')

    start = time.time()
    for i in range(nmessages):
        client.send(payload)
        assert client.recv() == payload

    end = time.time()
    print(nmessages / (end - start), 'messages/sec')


if __name__ == '__main__':
    main("tcp://localhost:5555", b'x', 10000)
