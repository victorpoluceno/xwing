import array
import socket
import asyncio

BUFFER_SIZE = 4096
SERVICE_POSITIVE_ANSWER = b'+'


async def listen(loop, unix_address, service):
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect(unix_address)
    sock.setblocking(False)

    await loop.sock_sendall(sock, bytes(service, encoding='utf-8'))
    response = await loop.sock_recv(sock, BUFFER_SIZE)
    if not response.startswith(SERVICE_POSITIVE_ANSWER):
        raise ConnectionError(response.decode().strip())  # NOQA

    return sock


async def accept(sock):
    while 1:
        try:
            _, ancdata, flags, addr = sock.recvmsg(1, BUFFER_SIZE)
            cmsg_level, cmsg_type, cmsg_data = ancdata[0]
        except BlockingIOError:
            await asyncio.sleep(0.1)
            continue
        else:
            break

    fda = array.array('I')
    fda.frombytes(cmsg_data)

    client = socket.fromfd(fda[0], socket.AF_INET, socket.SOCK_STREAM)
    client.sendall(SERVICE_POSITIVE_ANSWER)
    client.setblocking(False)
    return client


async def connect(loop, tcp_address, service, tcp_nodelay=True):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if tcp_nodelay:
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    sock.connect(tcp_address)
    await loop.sock_sendall(sock, bytes(service, encoding='utf-8'))
    response = sock.recv(BUFFER_SIZE)
    if response != SERVICE_POSITIVE_ANSWER:
        raise ConnectionError(response.decode().strip())  # NOQA

    return sock


async def send(loop, sock, data):
    return await loop.sock_sendall(sock, data)


async def recv(loop, sock):
    return await loop.sock_recv(sock, BUFFER_SIZE)
