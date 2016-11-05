from xwing.node import init_node, start_node, spawn


class Server(object):

    def hello_world(self):
        return 'Hello World!'

    def run(self):
        async def rpc_server(mailbox, server):
            while True:
                function, pid = await mailbox.recv()
                print('Got call from: ', pid)

                result = getattr(server, function)()
                await mailbox.send(pid, result)

        spawn(rpc_server, self, name='rpc_server')


class Client(object):

    def __init__(self, server_pid):
        self.server_pid = server_pid

    def call(self, function):
        async def dispatch(mailbox, function):
            await mailbox.send(self.server_pid, function, mailbox.pid)
            result = await mailbox.recv()
            print('Got result: ', result)

        spawn(dispatch, function)


if __name__ == '__main__':
    # python examples/mailbox/rpc.py
    init_node()

    server = Server()
    server.run()

    client = Client('rpc_server@127.0.0.1')
    client.call('hello_world')

    start_node()
