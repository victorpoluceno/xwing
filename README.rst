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

References
----------

	- http://zguide.zeromq.org/page:all#Robust-Reliable-Queuing-Paranoid-Pirate-Pattern
	- http://zguide.zeromq.org/py:lpclient
	- http://zguide.zeromq.org/py:ppqueue
	- http://zguide.zeromq.org/py:ppworker

TODO
----

	- Improve README using tcpmux format
	- Implement server tests of heartbeating and reconnecting.
	- Change names to sender/receiver.
	- Move the basic example to one file.
	- Implement a check sum on replies.
	- Add an initial benchmark.
	- Add a failure test simulation.