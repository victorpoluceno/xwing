import asyncio
from unittest import mock


def run(loop, coro_or_future):
    return loop.run_until_complete(coro_or_future)


def run_until_complete(f):
    def wrap(*args, **kwargs):
        return run(asyncio.get_event_loop(), f(*args, **kwargs))
    return wrap


def make_coro_mock():
    coro = mock.Mock(name="CoroutineResult")
    corofunc = mock.Mock(name="CoroutineFunction",
                         side_effect=asyncio.coroutine(coro))
    corofunc.coro = coro
    return corofunc


def run_once(f, return_value=None):
    def wrapper(*args, **kwargs):
        if not wrapper.has_run:
            wrapper.has_run = True
            return f(*args, **kwargs)
        return return_value
    wrapper.has_run = False
    return wrapper


class SynteticBuffer:

    def __init__(self):
        self.buffer = []

    def put(self, data):
        self.buffer.append(data)

    def pop(self):
        return self.buffer.pop()

syntetic_buffer = SynteticBuffer()
