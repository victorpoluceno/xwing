import sys
sys.path.append('.')

from xwing.server import Server


def handle_message(server, message):
    server.send(message)


if __name__ == '__main__':
    server = Server("ipc:///tmp/0", sys.argv[1])
    server.on_recv(handle_message)
    server.run()
