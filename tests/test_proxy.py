from gevent import monkey
monkey.patch_all()

import sys
sys.path.append('.')

import logging
logging.basicConfig(level=logging.DEBUG)

from xwing.proxy import Proxy


class TestProxy(object):

    def test_run(self):
        proxy = Proxy('tcp://*:5555', 'ipc:///tmp/0')
        proxy.run()
