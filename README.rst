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

Usage
-----

Bootstraping::

	pyvenv env
	source env/bin/activate
	pip install -r requirements.txt


References
----------

	- http://zguide.zeromq.org/page:all#Robust-Reliable-Queuing-Paranoid-Pirate-Pattern
	- http://zguide.zeromq.org/py:lpclient
	- http://zguide.zeromq.org/py:ppqueue
	- http://zguide.zeromq.org/py:ppworker

TODO
----

	- Implement server to proxy heartbeat.
	- Implement server tests of heartbeating and reconnecting.
	- Implement tests for the proxy to proxy feature.
	- Change names to sender/receiver.
	- Move the basic example to one file.
	- Implement a check sum on replies.
	- Add an initial benchmark.
	- Add a failure test simulation.