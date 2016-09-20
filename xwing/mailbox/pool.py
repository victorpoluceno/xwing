class Pool(object):

    def __init__(self):
        self._connections = {}

    def get(self, identity):
        return self[identity]

    def add(self, identity, conn):
        assert not self._connections.get(identity)
        self._connections[identity] = conn

    def __getitem__(self, item):
        if not isinstance(item, str):
            raise TypeError('Item must be of str type')
        return self._connections[item]

    def __contains__(self, item):
        try:
            self.__getitem__(item)
        except KeyError:
            return False
        return True
