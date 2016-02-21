from gevent import monkey
monkey.patch_all()

import sys
sys.path.append('.')

from xwing.proxy import Proxy


if __name__ == '__main__':
    print(sys.argv)
    frontend, backend = sys.argv[1:]
    proxy = Proxy("tcp://*:{0}".format(frontend),
                  "ipc:///tmp/{0}".format(backend))
    proxy.run()

    try:
        proxy.join()
    except KeyboardInterrupt:
        pass
