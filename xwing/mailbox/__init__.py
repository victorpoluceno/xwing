import pickle
import uuid
import asyncio

from xwing.network.connection_pool import ConnectionPool
from xwing.network.protocol.inbound import Inbound
from xwing.network.protocol.outbound import Outbound


def resolve(name_or_pid):
    if isinstance(name_or_pid, str):
        if '@' in name_or_pid:
            name, hub_address = name_or_pid.split('@')
            return hub_address, name
        else:
            return '127.0.0.1', name_or_pid

    return name_or_pid


class Mailbox(object):

    def __init__(self, hub_frontend, hub_backend, loop, name):
        self.hub_backend = hub_backend
        self.hub_frontend = hub_frontend
        self.loop = loop
        self.identity = name if name else str(uuid.uuid1())
        self.connection_pool = ConnectionPool()
        self.inbound = Inbound(self.loop, self.hub_backend, self.identity,
                               self.connection_pool)
        self.outbound = Outbound(self.loop, self.identity,
                                 self.connection_pool, self.inbound)

    def start(self):
        self.loop.create_task(self.inbound.start())
        self.outbound.start()

    def stop(self):
        self.inbound.stop()
        self.outbound.stop()

    @property
    def pid(self):
        return self.hub_frontend, self.identity

    async def recv(self, timeout=None):
        payload = await self.inbound.recv(timeout=timeout)
        return pickle.loads(payload)

    async def send(self, name_or_pid, *args):
        payload = pickle.dumps(args)
        pid = resolve(name_or_pid)
        await self.outbound.send(pid, payload)


class Node(object):

    def __init__(self, loop=None, hub_frontend='127.0.0.1',
                 hub_backend='/var/tmp/xwing.socket'):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.hub_frontend = hub_frontend
        self.hub_backend = hub_backend
        self.mailbox_list = []
        self.tasks = []


node_ref = None


def get_node_instance():
    global node_ref
    return node_ref


def init_node():
    global node_ref
    node_ref = Node()


def spawn(fn, *args, name=None, node=None):
    if not node:
        node = get_node_instance()

    # Create a mailbox for my upper_actor and schedule it to run
    mailbox = Mailbox(node.hub_frontend, node.hub_backend,
                      node.loop, name)
    mailbox.start()

    node.tasks.append(node.loop.create_task(fn(mailbox, *args)))
    node.mailbox_list.append(mailbox)
    return mailbox.pid


def start_node(node=None):
    '''Start node loop, by running all actors.'''
    if not node:
        node = get_node_instance()

    try:
        done, pending = node.loop.run_until_complete(asyncio.wait(
            node.tasks, return_when=asyncio.FIRST_EXCEPTION))

        # If a exception happened on any of waited tasks
        # this forces the exception to buble up
        for future in done:
            future.result()
    finally:
        stop_node()


def stop_node(node=None):
    '''Graceful node stop.

    Cancel all running actors and wait for them to finish before
    stopping.'''
    if not node:
        node = get_node_instance()

    for task in asyncio.Task.all_tasks():
        task.cancel()

    try:
        pending = asyncio.Task.all_tasks()
        node.loop.run_until_complete(asyncio.wait(pending))
    except RuntimeError:
        # Ignore RuntimeErrors like loop is already closed.
        # It may happens in KeyboardInterrupt exception for
        # example, as asyncio already killed the event loop.
        pass
