import asyncio
from unittest import mock


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
