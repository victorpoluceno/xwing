import pickle

from xwing.network.controller import Controller
from xwing.network.transport.stream.client import get_stream_client
from xwing.network.transport.stream.server import get_stream_server


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
        self.controller = Controller(loop, settings, self.task_pool,
                                     get_stream_client('real'),
                                     get_stream_server('real'))

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
