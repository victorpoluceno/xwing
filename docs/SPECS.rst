XWing
=====

Multiplexing, fowarding, route.

Requirements
============

- Implement a MULTIPLEX process, that knowns how to ROUTE messages to its local connected PEERS and answer back to CLIENTS.

- Be able to implement HEARTBEATS between the MULTIPLEX process and the LOCAL connected peers, in both ways.

- Capacity to have persistent connections between CLIENTS and the MULTIPLEX process.

- The MULTIPLEX process must knonw how to send requests from it's local PEERS to others MULTIPLEX process.

Proxy
-----

The proxy implements the routing part and it expects communication with both client and server.

For both the frontend, where the clients connect, and the backend, where the server connects, the proxy uses a ZeroMQ ROUTER socket type. The proxy receives a request on the frontend it will get the payload and route it to the right server thorugh the backend. Also if the proxy receives and reponse on the backend it will send it to the right client on the frontend.

In order to first open the socket connection and to keep a list of servers, the proxy keeps a list of live servers and when a server connects it sends a READ signal, this way the proxy may add this server to the server list.

To avoid stalled connection to servers, the proxy sends Heartbeats to all of it is known servers. So if a server is stalled it will miss Heartbeats and may well reconnect.

The proxy also receives Heartbeats from the server, this it may keep a list of all known health servers. [TODO]

All connection from both frontend and backend and persistent, the proxy always keeps connections open.

Server
------

The Server implements reply part and it expects communinction with a proxy. The server must be unique identified, so the socket known how is answer.

The socket used is a ZeroMQ DEALER type. The DEALER socket does not require and recv aftet a send, witch is a handy for Heartbeat implementation. The server receives an request and always send an answer back, with CRC of the sent payload, alongside the response. [TODO]

In order to start receiveng requests the server MUST send a ready signal to the proxy, that tells the proxy that this servers is accepting requests.

The server keeps a loop listening for incoming requests, to avoid having a frozen or stalled socket the server implments a Heartbead to proxy in both directions. It both need to receive and Heartbead from proxy and also send a heartbeat to proxy. The Heartbeat implementation avoids unicessary data transferred by considering any non Heartbeat comunnications as a Heartbeat too. After a configured number of Heratbeats are missing, the server tries to reconnect to socket after sleeping for configured interval. The sleep interval is exponenintal raised up to a configured max value when it will stay reconnectin and sleeping forever. 

At this moment there is no API or option to force a exception after the max interval is excced. [FUTURE]

The server also need to send Heartbeats to the proxy on a configured interval. Those Hearbeats signsl are fire and forget. [TODO]

The server to proxy connection is persistent, once stabilished it will no closed until the program ends.

Client
------

The Client implements the request part and it expects comunnication with a proxy. The client must be unique identified, so the socket may known for whom to send an answer to. The client always send a to a server and so must known server unique id.

The socket used is a ZeroMQ REQ socket type. The ZeroMQ REQ socket is required to have an recv after a send. So the client implements a send of a payload and always expects to receive an reply with a CRC of the sent payload back whiting the response. 

The client implements a retry semantics, after a request is sent it will wait for answer to be received inside a timeout interval, if an answer does not arrive, or arrive corrupted the client retries, by reconnecting and sending the data back, and then repeats this until an answer is received or a number of retries is exced. If the number of retries is excced the clients stop trying and raise and exception.

In this sense, the communication is always at least once. To change that behaviour or may set number of retries to 0. [THINK ABOUT THIS]

The retry implementation and the send and recv semantics does not offer a non blocking API for now. [FUTURE]

The client to proxy connections short lived, once the progtams send and receives and answer the connections is closed.

References
----------

	- http://zguide.zeromq.org/page:all#Robust-Reliable-Queuing-Paranoid-Pirate-Pattern
	- http://zguide.zeromq.org/py:lpclient
	- http://zguide.zeromq.org/py:ppqueue
	- http://zguide.zeromq.org/py:ppworker