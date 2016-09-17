xwing
=====

.. image:: https://travis-ci.org/victorpoluceno/xwing.svg?branch=development
    :target: https://travis-ci.org/victorpoluceno/xwing

|

Python based *asyncio* Actor Framework.

**xwing** is a full featured actor framework inspired by Erlang's design. 

Features
--------

* Simple. Ships with a minimal for humans actor API.
* Fast. Message multiplexing implemented by routing connections, not data.
* Powerful. Based and inspired by the battle tested Erlang's actor design.
* High level. Allow developers to write applications without worrying too much about low level details.
* Interoperable. Can live along side other async libraries or applications.
* Rich. Packed with features that are essential to write distributed applications.

Sample
------

.. code-block:: python

    from xwing.mailbox import init_node, start_node, spawn

    async def pong(mailbox):
        message, pid = await mailbox.recv()
        await mailbox.send(pid, 'pong')

    async def ping(mailbox, pong_pid):
        await mailbox.send(pong_pid, 'ping', mailbox.pid)
        print(await mailbox.recv())

    init_node()
    pong_pid = spawn(pong)
    spawn(ping, pong_pid)
    start_node()

Status
------

Not released, under heavy development. **Unstable API**.

Requirements
------------

Xwing requires Python 3.5+.

Roadmap
-------

Features planned to *0.1* release:

* Task Scheduler with SMP support.
* Auto start of Xwing Hub on Node start.
* Heartbeat for connection check and keepalive.
* Full tested and benchmarked uvloop support.

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
