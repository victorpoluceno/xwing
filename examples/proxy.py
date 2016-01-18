import sys
sys.path.append('.')

from xwing.proxy import Proxy


if __name__ == '__main__':
    server = Proxy("tcp://*:5555", "ipc:///tmp/0")
    server.start()
