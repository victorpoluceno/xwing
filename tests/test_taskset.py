import asyncio

from xwing.concurrency.taskset import TaskSet
from tests.helpers import run_until_complete


class TestTaskSet:

    def setup_method(self, method):
        self.loop = asyncio.get_event_loop()
        self.taskset = TaskSet(self.loop)

    @run_until_complete
    async def test_task_exception_invoke_callbacks(self):
        async def run_and_raise():
            raise Exception

        called = []

        def check_raise(fut):
            called.append(True)

        self.taskset.add_exception_callback(check_raise)
        self.taskset.add_exception_callback(check_raise)
        task = self.taskset.create_task(run_and_raise())
        await asyncio.wait([task])
        assert called and len(called) == 2
