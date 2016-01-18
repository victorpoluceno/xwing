import sys
sys.path.append('.')

from xwing.naked_server import Server


def handle_message(server, message):
    server.send(message)


if __name__ == '__main__':
    server = Server("tcp://*:5555", sys.argv[1])
    server.on_recv(handle_message)
    server.run()
