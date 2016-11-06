class TaskSet:

    def __init__(self, loop):
        self.loop = loop
        self.callbacks = []

    def create_task(self, fn):
        task = self.loop.create_task(fn)
        task.add_done_callback(self.done_callback)
        return task

    def done_callback(self, fut):
        if not fut.cancelled() and fut.exception:
            for callback in self.callbacks:
                callback(fut)

    def add_exception_callback(self, callback):
        self.callbacks.append(callback)
