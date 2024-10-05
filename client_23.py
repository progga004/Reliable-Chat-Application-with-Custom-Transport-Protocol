'''
This module defines the behaviour of a client in your Chat Application
'''
import sys
import getopt
import socket
import random
from threading import Thread,Event
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
        self.stop = False  
        self.window_size = window_size
        # self.seq_num = random.randint(0, 65535)
        self.seq_num=1
        self.ack_received = False
        self.ack_event = Event()
    
    def start(self):
            print("Attem")
            self.join_chat()
            while not self.stop:
                user_input = input().strip()
                parts = user_input.split(' ', 2)
                command = parts[0]

                if command == 'msg':
                    num_users = int(parts[1])
                    remaining_input = parts[2]
                    usernames_and_message = remaining_input.split(' ', num_users)
                    usernames = usernames_and_message[:num_users]
                    message = ' '.join(usernames_and_message[num_users:])
                    msg_data = f"{self.name} {num_users} {' '.join(usernames)} {message}"
                    print("Message data",msg_data)
                    if self.send_data(f"msg {msg_data}"):
                        self.send_end()

                elif command == 'list':
                    if self.send_data(f"request_users_list {self.name}"):
                        self.send_end()

                elif command == 'quit':
                    if self.send_data(f"disconnect {self.name}"):
                        self.send_end()
                    print("quitting")
                    self.stop = True

                elif command == 'help':
                    print("msg <number_of_users> <username1> <username2> … <message>")
                    print("list")
                    print("help")
                    print("quit")

                else:
                    print("incorrect user input format")
                    if self.send_data(f"unknown_command {self.name} {command}"):
                        self.send_end()

    def receive_handler(self):
        while not self.stop:
            try:
                message, _ = self.sock.recvfrom(1024)
                msg_type, seq_num, data, checksum = parse_packet(message.decode('utf-8'))
                print("Checking coming in receive handler",msg_type, seq_num, data, checksum)
                if msg_type == 'ack' and int(seq_num) == self.seq_num + 1:
                    self.seq_num += 1
                    ack_received = True

                if msg_type == 'forward_message':
                    print(f"msg: {data}")

                elif msg_type == 'response_users_list':
                    print(f"list: {data}")

                elif msg_type in {'ERR_SERVER_FULL', 'ERR_USERNAME_UNAVAILABLE'}:
                    print("disconnected:", msg_type.lower().replace('_', ' '))
                    self.stop = True

            except socket.timeout:
                continue

    def send_packet_and_wait_ack(self, packet):
        ack_received = False
        while not ack_received:
            self.sock.sendto(packet.encode('utf-8'), (self.server_addr, self.server_port))
            try:
                response, _ = self.sock.recvfrom(1024)
                msg_type, seq_num, _, _ = parse_packet(response.decode('utf-8'))
                print("Message coming from receiver",msg_type, seq_num, _, _)
                if msg_type == 'ack' and int(seq_num) == self.seq_num + 1:
                    ack_received = True
                    self.seq_num += 1
            except socket.timeout:
                continue
        return ack_received
    
    def join_chat(self):
      print("Am I here in join chat")
      if self.send_start():
        join_data = f"join {self.name}"
        print("Join data",join_data)
        data_packet = make_packet('data', self.seq_num, join_data)
        print("Data packet sent",data_packet,self.seq_num, join_data)
        ack_received = False
        while not ack_received:
            self.sock.sendto(data_packet.encode('utf-8'), (self.server_addr, self.server_port))

        if self.send_packet_and_wait_ack(data_packet):
            end_packet = make_packet('end', self.seq_num, '')
            print("End packet sending",end_packet,self.seq_num)
            if self.send_packet_and_wait_ack(end_packet):
                print(f"Join successful: {self.name}")
            else:
                print("Failed to end join session properly.")
        else:
            print("Failed to send join data, will not send end.")
      else:
        print("Failed to start join session, cannot proceed.")


    def send_start(self):
        packet = make_packet('start', self.seq_num, '')
        print("Start packet",packet,self.seq_num)
        return self.send_packet_and_wait_ack(packet)

    def send_data(self, data):
        packet = make_packet('data', self.seq_num, data)
        print("Data packet",packet,self.seq_num)
        return self.send_packet_and_wait_ack(packet)

    def send_end(self):
        packet = make_packet('end', self.seq_num, '')
        print("End packet",packet,self.seq_num)
        return self.send_packet_and_wait_ack(packet)

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
