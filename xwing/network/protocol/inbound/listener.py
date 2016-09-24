import asyncio
import logging
log = logging.getLogger(__name__)

from xwing.network.transport.stream.server import StreamServer


class Listener(object):

    def __init__(self, loop, hub_backend, identity):
        self.loop = loop
        self.identity = identity
        self.server = StreamServer(loop, hub_backend, identity)

    async def listen(self):
        await self.server.listen()
        log.info('%s is listening.' % self.identity)

    async def accept(self, timeout):
        try:
            stream = await asyncio.wait_for(
                self.server.accept(), timeout)
        except asyncio.TimeoutError:
            return None

        return stream
