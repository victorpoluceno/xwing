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
