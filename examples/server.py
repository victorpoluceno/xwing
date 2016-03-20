import sys
sys.path.append('.')

import logging
logging.basicConfig(level='DEBUG')

from xwing.server import SocketServer

# python examples/simple/server.py ipc:///tmp/0 0

if __name__ == '__main__':
    print(sys.argv)
    proxy_endpoint, identity = sys.argv[1:]

    socket_server = SocketServer(proxy_endpoint, identity)
    socket_server.bind()
    while True:
        data = socket_server.recv()
        socket_server.send(data)
