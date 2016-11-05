import asyncio
import uuid
from functools import partial

import attr

from xwing.concurrency import Mailbox


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
