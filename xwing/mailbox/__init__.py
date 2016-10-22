import pickle
import uuid
import asyncio
from functools import partial
import asyncio

import attr

from xwing.network.controller import Controller


def resolve(name_or_pid):
    if isinstance(name_or_pid, str):
        if '@' in name_or_pid:
            name, hub_address = name_or_pid.split('@')
            return hub_address, name
        else:
            return '127.0.0.1', name_or_pid

    return name_or_pid


class TaskPool:

    def __init__(self, loop):
        self.loop = loop
        self.callbacks = []

    def create_task(self, fn):
        fut = self.loop.create_task(fn)
        fut.add_done_callback(self.done_callback)

    def done_callback(self, fut):
        if not fut.cancelled() and fut.exception:
            for callback in self.callbacks:
                callback(fut)

    def add_exception_callback(self, callback):
        self.callbacks.append(callback)


class Mailbox(object):

    def __init__(self, loop, settings):
        self.loop = loop
        self.settings = settings
        self.task_pool = TaskPool(loop)
        self.controller = Controller(loop, settings, self.task_pool)

    def start(self):
        self.controller.start()

    def stop(self):
        self.controller.stop()

    @property
    def pid(self):
        return self.settings.hub_frontend, self.settings.identity

    async def recv(self, timeout=None):
        payload = await self.controller.get_inbound(timeout=timeout)
        return pickle.loads(payload)

    async def send(self, name_or_pid, *args):
        payload = pickle.dumps(args)
        pid = resolve(name_or_pid)
        await self.controller.put_outbound(pid, payload)


@attr.s
class Settings(object):
    hub_frontend = attr.ib(default='127.0.0.1:5555')
    hub_backend = attr.ib(default='/var/tmp/xwing.socket')
    identity = attr.ib(default=attr.Factory(uuid.uuid1), convert=str)


class Node(object):

    def __init__(self, loop=None, settings={}):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.settings = Settings(**settings)
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

    if name:
        node.settings.identity = name

    mailbox = Mailbox(node.loop, node.settings)
    mailbox.start()

    # FIXME right now we need this to make sure that
    # the finished messages is sent before the actor
    # exit and its mailbox gets garbaged. How does
    # Erlang fix this problem?

    async def wrap(fn, mailbox, *args):
        ret = await fn(mailbox, *args)
        await asyncio.sleep(0.1)
        return ret

    task = node.loop.create_task(wrap(fn, mailbox, *args))
    node.tasks.append(task)

    def finish(process, fut):
        process.set_exception(fut.exception())

    mailbox.task_pool.add_exception_callback(partial(finish, task))
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
