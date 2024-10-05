### Overview
In this chat application, there will be one server and multiple clients. The clients are the users of the chat application. All clients must implement the functionality needed to reliably exchange messages. In this architecture, we will use a central server to keep track of which users are active and how to reach individual users. The server knows all the clients that are currently active (i.e., can receive and send messages) and how to reach them (i.e. current address). All message exchanges happen through the server. A client (e.g., Client1) that wants to send a message to another client (e.g., Client2), first sends the message to the server, which then sends it to the destined client.

### Features
- A simple chat application using UDP, which is a transport protocol that does not ensure reliable communication.
- Extending the chat application to implement sequences and acknowledgements just like TCP.
- Extending the chat application to ensure reliable communication of messages in case of packet loss

### Instructions on how to run the program
To run the server of chat application, execute following command:
```bash
$ python3 server.py -p <port_num>
```
Similarly, execute following command to run a client (with same port_num that you have provided to server.py):
```bash
$ python3 client.py -p <server_port_num> -u <username>
```
