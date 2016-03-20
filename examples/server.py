from gevent import monkey
monkey.patch_all()

import sys
sys.path.append('.')

from xwing.server import Server


if __name__ == '__main__':
    print(sys.argv)
    proxy_endpoint, identity = sys.argv[1:]
    server = Server("ipc:///tmp/{0}".format(proxy_endpoint), identity)
    server.run()

    try:
        while True:
            server.recv()
    except KeyboardInterrupt:
        pass
