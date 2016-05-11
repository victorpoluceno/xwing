import sys
sys.path.append('.')

import logging
logging.basicConfig(level='DEBUG')

from xwing.socket.server import Server

# python examples/server.py /var/tmp/xwing.socket server0

if __name__ == '__main__':
    print(sys.argv)
    proxy_endpoint, identity = sys.argv[1:]

    socket_server = Server(proxy_endpoint, identity)
    socket_server.listen()
    conn = socket_server.accept()

    while True:
        data = conn.recv()
        conn.send(data)
