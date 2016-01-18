import sys
sys.path.append('.')

import time

from xwing.naked_client import Client


def main(endpoint, payload, nmessages, identity):
    print("I: Starting send loop...")
    client = Client(endpoint, identity)

    start = time.time()
    for i in range(nmessages):
        # FIXME implement case where we recive no answer
        # or a bad one
        client.send(payload)

    end = time.time()
    print(nmessages / (end - start), 'messages/sec')


if __name__ == '__main__':
    main("tcp://localhost:5555", b'x', 10000, 'client')
