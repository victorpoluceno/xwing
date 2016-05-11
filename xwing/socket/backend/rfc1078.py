import array
import socket

BUFFER_SIZE = 4096
SERVICE_POSITIVE_ANSWER = b'+'


def listen(unix_address, service):
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect(unix_address)
    sock.sendall(bytes(service, encoding='utf-8'))
    response = sock.recv(BUFFER_SIZE)
    if not response.startswith(SERVICE_POSITIVE_ANSWER):
        raise ConnectionError(response.decode().strip())  # NOQA

    return sock


def accept(sock):
    _, ancdata, flags, addr = sock.recvmsg(1, BUFFER_SIZE)
    cmsg_level, cmsg_type, cmsg_data = ancdata[0]

    fda = array.array('I')
    fda.frombytes(cmsg_data)

    client = socket.fromfd(fda[0], socket.AF_INET, socket.SOCK_STREAM)
    client.send(SERVICE_POSITIVE_ANSWER)
    client.setblocking(True)
    return client


def connect(tcp_address, service, tcp_nodelay=True):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if tcp_nodelay:
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    sock.connect(tcp_address)
    sock.sendall(bytes(service, encoding='utf-8'))
    response = sock.recv(BUFFER_SIZE)
    if response != SERVICE_POSITIVE_ANSWER:
        raise ConnectionError(response.decode().strip())  # NOQA

    return sock


def send(sock, data):
    return sock.sendall(data)


def recv(sock):
    return sock.recv(BUFFER_SIZE)
