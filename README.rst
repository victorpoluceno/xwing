xwing
=====

Python 3 implementation of a TCP multiplexer.

Xwing is a Python library that helps to distribute connections to a single port to other multiple process.

Xwing uses ZeroMQ as communicaton layer.

Features
--------

Xwing features:

  * Support to all ZeroMQ protocols.
  * API componentes designed to be embeded.

Requirements
------------

Xwing requires Python 3.4+ and ZeroMQ.

Usage
-----

Installation
~~~~~~~~~~~~

  pip install xwing

Running the Proxy
~~~~~~~~~~~~~~~~~

Xwing ships a standalone proxy daemon ready to be used. Proxy will start listening on port 5555 for client connections. Here is how to run the proxy daemon::

  xwing

Server implementation
~~~~~~~~~~~~~~~~~~~~~

The serve connects to proxy as a server and start waiting to answer clients. Here is a server implementation::

  from xwing.server import SocketServer

  server = Server("ipc:///tmp/0", "server0")
  server.bind()
  ping = server.recv()
  server.send(pong)

Client implementation
~~~~~~~~~~~~~~~~~~~~~

Client connects to proxy daemon and send a data. Here is the Client implementation::

  from xwing.client import SocketClient

  client = Client("tcp://localhost:5555")
  client.send("server0", "ping")
  print(client.recv())

Development
----------

Bootstraping
~~~~~~~~~~~~

Create a venv and install development requirements::

  pyvenv env && source env/bin/activate
  pip install -e .

Testing
~~~~~~~

Run using `py.test`::

  py.test tests

Or if you want to see coverage report::

  pip install pytest-cov
  py.test --cov=xwing --cov-report html tests/
  open htmlcov/index.html

License
-------

The software is licensed under ISC license.
