import sys
sys.path.append('.')

import time

from xwing.socket.client import Client

# python examples/client.py


def main(endpoint, payload, nmessages):
    print("Starting send loop...")
    client = Client(endpoint)
    conn = client.connect('server0')

    start = time.time()
    for i in range(nmessages):
        conn.send(payload)
        assert conn.recv() == payload

    end = time.time()
    print(nmessages / (end - start), 'messages/sec')


if __name__ == '__main__':
    main("localhost:5555", b'x', 10000)
