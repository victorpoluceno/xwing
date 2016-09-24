import asyncio
import logging
log = logging.getLogger(__name__)

from xwing.network import SEPARATOR


class Receiver(object):

    def __init__(self, loop, identity):
        self.loop = loop
        self.identity = identity

    async def recv(self, reader, timeout):
        try:
            data = await asyncio.wait_for(reader.readline(), timeout)
        except asyncio.TimeoutError:
            return None

        if data and not data.endswith(SEPARATOR):
            log.warning('Received a partial message. '
                        'This may indicate a broken pipe.')
            # TODO may be we need to raise an exception here
            # and only return None when connection is really closed?
            return None

        return data[:-1]
