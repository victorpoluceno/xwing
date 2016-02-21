from gevent import monkey
monkey.patch_all()

import sys
sys.path.append('.')

import time
import random

from xwing.client import Client


def main(endpoint, payload, nmessages):
    print("I: Starting send loop...")
    client = Client(endpoint)

    start = time.time()
    for i in range(nmessages):
        server = random.choice(['0', '1'])
        client.send(server, payload)

    end = time.time()
    print(nmessages / (end - start), 'messages/sec')


if __name__ == '__main__':
    main("tcp://localhost:5555", 'x', 10000)
