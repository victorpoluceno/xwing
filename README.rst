XWING
=====

Blazing fast Python 3 multiplexing and communication library.

Features
--------

  * Server mutliplexing througth proxy.
  * Multi protocol support.
  * Client retry support.
  * Heartbeat and reconnect support.
  * Route throught proxy support.
  * Reply check sum.
  * Small parts that can be used to form complex toplogies.

Requirements
------------

Xwing uses Python 3.4+.

Usage
-----

Bootstraping::

	pyvenv env
	source env/bin/activate
	pip install -r requirements.txt


Testing
-------

Run using py.test::

	py.test tests

Or if you want to see the coverage report::

	py.test --cov=xwing --cov-report tests/
	open htmlcov/index.html

TODO
----

	- Refactoring ZMQ stuff on its on class.
	- Implement tests of client retry strategy.
	- Implement a check sum on replies.
	- Improve README using tcpmux format
	- Change names to sender/receiver.
	- Add an initial benchmark.
	- Add a failure test simulation.
	- Think about current infinity buffer size.
