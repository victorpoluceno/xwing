import array
import socket
import asyncio

BUFFER_SIZE = 4096
SERVICE_POSITIVE_ANSWER = b'+'
SERVICE_PING = b'!'

# FIXME implement a shared buffer beteween listening and
# accept, this way listening may get pings and accept
# may get its file descriptors, avoiding this way the
# problem that a socket not issuing accepts may hold
# a service id forever.


async def listen(loop, unix_address, service):
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.setblocking(False)
    await loop.sock_connect(sock, unix_address)
    await loop.sock_sendall(sock, bytes(service, encoding='utf-8'))
    response = await loop.sock_recv(sock, BUFFER_SIZE)
    if not response.startswith(SERVICE_POSITIVE_ANSWER):
        raise ConnectionError(response.decode().strip())  # NOQA

    return sock


async def accept(loop, sock):
    while True:
        try:
            data = sock.recvmsg(1, BUFFER_SIZE)
            # In order to be able to tell if a server is alive or not
            # the hub send a ping message to server in case some one
            # try to connect using same service name. In this case
            # We can just ignore this data.
            #
            # Be aware that current implementation will only allow
            # this ping mechancis to work after user start accepting
            # connections, so a Server listening without accepting
            # will hold this service forever.
            if data[0] == SERVICE_PING:
                continue
            _, ancdata, flags, addr = data
            if not ancdata:
                # Hub is gone, return None will signal that listen must run
                # again. We also close the socket, this way any further
                # operations on this socket will raise OSError
                sock.close()
                return None

            cmsg_level, cmsg_type, cmsg_data = ancdata[0]
        except BlockingIOError:
            await asyncio.sleep(0.1)
            continue
        else:
            break

    fda = array.array('I')
    fda.frombytes(cmsg_data)

    client = socket.fromfd(fda[0], socket.AF_INET, socket.SOCK_STREAM)
    client.setblocking(False)

    await loop.sock_sendall(client, SERVICE_POSITIVE_ANSWER)
    return client


async def connect(loop, tcp_address, service, tcp_nodelay=True):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if tcp_nodelay:
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    sock.setblocking(False)
    await loop.sock_connect(sock, tcp_address)
    await loop.sock_sendall(sock, bytes(service, encoding='utf-8'))
    response = await loop.sock_recv(sock, BUFFER_SIZE)
    if response != SERVICE_POSITIVE_ANSWER:
        raise ConnectionError(response.decode().strip())  # NOQA

    return sock


async def send(loop, sock, data):
    ret = await loop.sock_sendall(sock, data)
    return True if ret is None else False

async def recv(loop, sock):
    return await loop.sock_recv(sock, BUFFER_SIZE)
