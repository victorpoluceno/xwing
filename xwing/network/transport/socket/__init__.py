from xwing.network.transport.socket.backend.rfc1078 import send, recv


class Connection:

    def __init__(self, loop, sock):
        self.loop = loop
        self.sock = sock

    async def recv(self):
        '''Try to recv data. If not data is recv NoData exception will
        raise.

        :param timeout: Timeout in seconds. `None` meaning forever.
        '''
        return await recv(self.loop, self.sock)

    async def recv_str(self, encoding='utf-8'):
        data = await self.recv()
        if encoding:
            data = data.decode(encoding)

        return data

    async def send(self, data):
        '''Send data to connected client.

        :param data: Data to send.
        '''
        return await send(self.loop, self.sock, data)

    async def send_str(self, data, encoding='utf-8'):
        if encoding:
            data = bytes(data, encoding)

        return await self.send(data)

    def close(self):
        self.sock.close()
