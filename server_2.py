'''
This module defines the behaviour of server in your Chat Application
'''
import sys
import getopt
import socket
from queue import Queue
from threading import Thread
# import util
from util import make_message,MAX_NUM_CLIENTS,make_packet,parse_packet,validate_checksum


class Server:
    '''
    This is the main Server Class. You will  write Server code inside this class.
    '''
    def __init__(self, dest, port, window):
        self.server_addr = dest
        self.server_port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.settimeout(None)
        self.sock.bind((self.server_addr, self.server_port))
        self.clients = {}
        self.expected_seqnums = {}
        self.message_queue = Queue()
        self.running = True
        self.message_buffers = {}
    
    def start(self):
        # print("Server is starting...")
        Thread(target=self.receive_messages).start()
        self.process_messages()


    def receive_messages(self):
        while self.running:
           
                message, client_addr = self.sock.recvfrom(1428)
                packet_type, seq_num, data, checksum = parse_packet(message.decode('utf-8'))
                # Validate the packet checksum
                if validate_checksum(message.decode('utf-8')):
                    self.message_queue.put((message, client_addr))
            
    def process_messages(self):
        while self.running:
            if not self.message_queue.empty():
                message, client_addr = self.message_queue.get()
                self.handle_packet(message, client_addr)
   
    def handle_packet(self, message, client_addr):

            packet_type, seq_num, data, checksum = parse_packet(message.decode('utf-8'))
            parts=data.split(' ', 2)
            command_type=parts[0]
            seq_num = int(seq_num)
            # Handle packet types
            if packet_type == 'start':
                self.expected_seqnums[client_addr] = seq_num + 1
                self.send_ack(client_addr, seq_num + 1)

            if packet_type == 'data':
             if command_type=='msg':
               

               command_type,index, total, chunk = self.parse_chunk_data(data)
               if client_addr not in self.message_buffers:
                self.message_buffers[client_addr] = {
                'chunks': {},
                'command_type': command_type
            }

               self.message_buffers[client_addr]['chunks'][index] = chunk

               if len(self.message_buffers[client_addr]['chunks']) == total:  # All chunks have been received
                chunks = [self.message_buffers[client_addr]['chunks'][i] for i in sorted(self.message_buffers[client_addr]['chunks'])]
                full_message = f"{self.message_buffers[client_addr]['command_type']} {' '.join(chunks)}"
                self.handle_data(client_addr, full_message)
                del self.message_buffers[client_addr]  # Clear buffer after processing
               self.send_ack(client_addr, seq_num+1)
             else:
                 if client_addr in self.expected_seqnums:
                    expected_seq_num = self.expected_seqnums[client_addr]
                    if seq_num == expected_seq_num:
                      self.handle_data(client_addr, data)
                      self.expected_seqnums[client_addr] += 1
                       
                   
                    self.send_ack(client_addr, self.expected_seqnums[client_addr])

            elif packet_type == 'end':
              if client_addr in self.expected_seqnums:
                expected_seq_num = self.expected_seqnums[client_addr]
                if seq_num == expected_seq_num:
                 self.send_ack(client_addr, seq_num + 1)
                 del self.expected_seqnums[client_addr]
              
       
            if client_addr in self.expected_seqnums and self.expected_seqnums[client_addr] <= seq_num:
            #  print(f"Packet {seq_num} acknowledged by {client_addr}, updating state")
             self.expected_seqnums[client_addr] = seq_num + 1

    def parse_chunk_data(self, data):
     parts = data.split(' ', 3)  # msg_type index total chunk_data
     command_type=parts[0]
     return command_type,int(parts[1]), int(parts[2]),parts[3]


    def send_ack(self, client_addr, seq_num):
        ack_packet = make_packet('ack', seq_num, '')
        # print("Ack packet made",ack_packet)
        self.sock.sendto(ack_packet.encode('utf-8'), client_addr)

    def handle_data(self, client_addr, data):
        parts = data.split(' ', 2)
        msg_type = parts[0]
        if msg_type == 'join':
            username = parts[1]
            if len(self.clients) >= MAX_NUM_CLIENTS:
                response = make_packet('data', 0, "ERR_SERVER_FULL")
                self.sock.sendto(response.encode('utf-8'), client_addr)
                print("disconnected: server full")
            elif username in self.clients:
                response = make_packet('data', 0, "ERR_USERNAME_UNAVAILABLE")
                self.sock.sendto(response.encode('utf-8'), client_addr)
                print("disconnected: username not available")
            else:
                self.clients[username] = client_addr
                print(f"join: {username}")

        elif msg_type == 'request_users_list':
            print(f"request_users_list: {parts[1]}")
            user_list = ' '.join(sorted(self.clients.keys()))
            response = make_packet('data', 0, f"response_users_list {len(user_list)} {user_list}")
            self.sock.sendto(response.encode('utf-8'), client_addr)

        elif msg_type == 'msg':
            sender, recipients_and_message = parts[1:]
            num_users_str, recipients_and_message = recipients_and_message.split(' ', 1)
            num_users = int(num_users_str)
            recipients_and_message_list = recipients_and_message.split(' ', num_users)
            recipients = recipients_and_message_list[:num_users]
            message = ' '.join(recipients_and_message_list[num_users:])
            for recipient in recipients:
                if recipient in self.clients:
                    forward_data = f"{sender}: {message}"
                    response = make_packet('data', 0, f"forward_message {forward_data}")
                    self.sock.sendto(response.encode('utf-8'), self.clients[recipient])
                    print(f"msg: {sender}")
                else:
                    print(f"msg: {sender} to non-existent user {recipient}")

        elif msg_type == 'disconnect':
            username = parts[1]
            if username in self.clients:
                del self.clients[username]
                print(f"disconnected: {username}")

# Do not change below part of code

if __name__ == "__main__":
    def helper():
        '''
        This function is just for the sake of our module completion
        '''
        print("Server")
        print("-p PORT | --port=PORT The server port, defaults to 15000")
        print("-a ADDRESS | --address=ADDRESS The server ip or hostname, defaults to localhost")
        print("-w WINDOW | --window=WINDOW The window size, default is 3")
        print("-h | --help Print this help")

    try:
        OPTS, ARGS = getopt.getopt(sys.argv[1:],
                                   "p:a:w", ["port=", "address=","window="])
    except getopt.GetoptError:
        helper()
        exit()

    PORT = 15000
    DEST = "localhost"
    WINDOW = 3

    for o, a in OPTS:
        if o in ("-p", "--port="):
            PORT = int(a)
        elif o in ("-a", "--address="):
            DEST = a
        elif o in ("-w", "--window="):
            WINDOW = a

    SERVER = Server(DEST, PORT,WINDOW)
    try:
        SERVER.start()
    except (KeyboardInterrupt, SystemExit):
        exit()
