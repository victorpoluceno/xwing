XWING
=====

Python 3 implementation of a TCP multiplexer.

XWING is a Python library writen using that help to distribute connect to a single port to other process.

XWING uses ZeroMQ as communicaton layer and gevent as async framework.

Features
--------

XWING features:

  * Out of the box heartbeat and reconnect support.
  * Request retry and reconnection support.
  * Support to all ZeroMQ protocols.
  * All componentes are designed to be embeded.

Requirements
------------

Xwing requires Python 3.4+, ZeroMQ and Gevent.

Usage
-----

  pip install xwing

Development
----------

Bootstraping
˜˜˜˜˜˜˜˜˜˜˜˜

Create a venv and install development requirements::

  pyvenv env && source env/bin/activate
  pip install -r dev-requirements.txt

Testing
˜˜˜˜˜˜˜

Run using `py.test`::

  py.test tests

Or if you want to see coverage report::

  py.test --cov=xwing --cov-report tests/
  open htmlcov/index.html

TODO
----

  - RCF implementation.
  - Change names to sender/receiver.
  - Refactoring ZMQ stuff on its on class.
  - Implement tests of client retry strategy.
  - Implement a check sum on replies.
  - Add an initial benchmark.
  - Add a failure test simulation.
  - Think about current infinity buffer size.
