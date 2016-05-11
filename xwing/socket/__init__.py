from xwing.socket.backend.rfc1078 import send, recv


class Connection:

    def __init__(self, sock):
        self.sock = sock

    def recv(self):
        '''Try to recv data. If not data is recv NoData exception will
        raise.

        :param timeout: Timeout in seconds. `None` meaning forever.
        '''
        return recv(self.sock)

    def recv_str(self, encoding='utf-8'):
        data = self.recv()
        if encoding:
            data = data.decode(encoding)

        return data

    def send(self, data):
        '''Send data to connected client.

        :param data: Data to send.
        '''
        send(self.sock, data)
        return True

    def send_str(self, data, encoding='utf-8'):
        if encoding:
            data = bytes(data, encoding)

        return self.send(data)
