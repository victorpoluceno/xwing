import sys
sys.path.append('.')

import time
import random

from xwing.client import Client

NETWORK = [(b'tcp://localhost:5555', b'bar'),
           (b'tcp://localhost:4444', b'foo')]


def main(endpoint, payload, nmessages, identity):
    print("I: Starting send loop...")
    client = Client(endpoint, identity)

    start = time.time()
    for i in range(nmessages):
        proxy, server = random.choice(NETWORK)
        client.send(server, payload, proxy=proxy)

    end = time.time()
    print(nmessages / (end - start), 'messages/sec')


if __name__ == '__main__':
    main(b"tcp://localhost:5555", b'x', 10000, b'client')
