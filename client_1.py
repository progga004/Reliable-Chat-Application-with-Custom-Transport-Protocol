'''
This module defines the behaviour of a client in your Chat Application
'''
import sys
import getopt
import socket
import random
from threading import Thread
import os
# import util
from util import make_message,make_packet,parse_packet

'''
Write your code inside this class. 
In the start() function, you will read user-input and act accordingly.
receive_handler() function is running another thread and you have to listen 
for incoming messages in this function.
'''

class Client:
    '''
    This is the main Client Class. 
    '''
    def __init__(self, username, dest, port, window_size):
        self.server_addr = dest
        self.server_port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(None)
        self.sock.bind(('', random.randint(10000, 40000)))
        self.name = username
        self.stop = False  # Add the stop flag
    
    def start(self):
        self.send_join()
        while True:
            user_input = input().strip()
            parts = user_input.split(' ', 2)
            command = parts[0]
            if command == 'msg':
                num_users = int(parts[1])
                
                remaining_input = parts[2]
                usernames_and_message = remaining_input.split(' ', num_users)
                usernames = usernames_and_message[:num_users]
                message = ' '.join(usernames_and_message[num_users:])
                msg_data = f"{self.name} {len(usernames)} {' '.join(usernames)} {message}"
               
                packet = make_packet('data', 0, f"msg {msg_data}")
                
                self.send(packet)

            elif command == 'list':
                packet = make_packet('data', 0, f"request_users_list {self.name}")
                self.send(packet)

            elif command == 'quit':
                packet = make_packet('data', 0, f"disconnect {self.name}")
                self.send(packet)
                print("quitting")
                break

            elif command == 'help':
                print("msg <number_of_users> <username1> <username2> … <message>")
                print("list")
                print("help")
                print("quit")

            else:
             packet = make_packet('data', 0, f"unknown_command {self.name} {command}")
             self.send(packet)
             print("incorrect userinput format")

    def receive_handler(self):
        while True:
            try:
                message, _ = self.sock.recvfrom(1024)
                packet_type, seq_num, data, checksum = parse_packet(message.decode('utf-8'))
                parts = data.split(' ', 2)
                msg_type = parts[0]
               
                if msg_type == 'forward_message':
                    print(f"msg: {parts[1]} {parts[2]}")

                elif msg_type == 'response_users_list':
                    print(f"list: {parts[2]}")
                elif msg_type == 'ERR_SERVER_FULL':
                    print("disconnected: server full")
                    self.stop=True
                    if self.stop:
                        self.sock.close()
                        sys.exit(0)
                    
                elif msg_type == 'ERR_USERNAME_UNAVAILABLE':
                    print("disconnected: username not available")
                    self.stop=True
                    if self.stop:
                        self.sock.close()
                        sys.exit(0)
                   
                elif msg_type == 'ERR_UNKNOWN_MESSAGE':
                  print("disconnected: server received an unknown command")
                  self.stop=True
                  if self.stop:
                        self.sock.close()
                        sys.exit(0)
                  
               
            except socket.timeout:
                continue

    def send(self, packet):
        self.sock.sendto(packet.encode('utf-8'), (self.server_addr, self.server_port))

    def send_join(self):
        packet = make_packet('data', 0, f"join {self.name}")
        self.send(packet)

# Do not change below part of code
if __name__ == "__main__":
    def helper():
        '''
        This function is just for the sake of our Client module completion
        '''
        print("Client")
        print("-u username | --user=username The username of Client")
        print("-p PORT | --port=PORT The server port, defaults to 15000")
        print("-a ADDRESS | --address=ADDRESS The server ip or hostname, defaults to localhost")
        print("-w WINDOW_SIZE | --window=WINDOW_SIZE The window_size, defaults to 3")
        print("-h | --help Print this help")
    try:
        OPTS, ARGS = getopt.getopt(sys.argv[1:],
                                   "u:p:a:w", ["user=", "port=", "address=","window="])
    except getopt.error:
        helper()
        exit(1)

    PORT = 15000
    DEST = "localhost"
    USER_NAME = None
    WINDOW_SIZE = 3
    for o, a in OPTS:
        if o in ("-u", "--user="):
            USER_NAME = a
        elif o in ("-p", "--port="):
            PORT = int(a)
        elif o in ("-a", "--address="):
            DEST = a
        elif o in ("-w", "--window="):
            WINDOW_SIZE = a

    if USER_NAME is None:
        print("Missing Username.")
        helper()
        exit(1)

    S = Client(USER_NAME, DEST, PORT, WINDOW_SIZE)
    try:
        # Start receiving Messages
        T = Thread(target=S.receive_handler)
        T.daemon = True
        T.start()
        # Start Client
        S.start()
    except (KeyboardInterrupt, SystemExit):
        sys.exit()
