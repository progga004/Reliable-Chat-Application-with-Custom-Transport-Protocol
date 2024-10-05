import sys
import getopt
import socket
import random
from threading import Thread,Lock,Event

from util import make_packet, parse_packet,CHUNK_SIZE

class Client:
    def __init__(self, username, dest, port, window_size):
        self.server_addr = dest
        self.server_port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(None)  # Set no timeout on the socket itself
        self.sock.bind(('', random.randint(10000, 40000)))
        self.name = username
        self.stop = False  
        self.window_size = window_size
        self.seq_num = random.randint(1, 10000)
        self.ack_received = False
        self.ack_received = {}
        self.lock = Lock()
        self.ack_event = Event()
        self.ack_count=0

    def start(self):
        if not self.join_chat():
            return
        
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
                self.handle_message(command,msg_data)
            elif command == 'list':
                data=f"request_users_list {self.name}"
                self.handle_message(command,data)
            elif command == 'quit':
                data=f"disconnect {self.name}"
                self.handle_message(command,data)
                self.send_end()
                print("quitting")
                break
            else:
               print("incorrect userinput format")
    def send_command(self, command_type, data=''):
     self.seq_num = random.randint(1, 10000)
     if not self.send_packet_and_wait_ack('start', f"{command_type} start"):
        return False

    # Send the data
    #  if command_type in 'msg': 
    #      chunks = [data[i:i + CHUNK_SIZE] for i in range(0, len(data), CHUNK_SIZE)]
    #      total_chunks = len(chunks)
    #      for index, chunk in enumerate(chunks):
    #        chunk_data = f"{command_type} {index} {len(chunks)} {chunk}"
    #     # Keep trying to send each chunk until it's acknowledged
    #        self.send_packet_and_wait_ack ('data', chunk_data)
    #         #  print(f"Retrying to send chunk {index} for {command_type}")
     if command_type == 'msg':
        data_bytes = data.encode('utf-8')  # Convert string to bytes
        chunks = [data_bytes[i:i + CHUNK_SIZE] for i in range(0, len(data_bytes), CHUNK_SIZE)]
        total_chunks = len(chunks)
        
        for index, chunk_bytes in enumerate(chunks):
            # Convert bytes back to string for transmission
            # Ensure UTF-8 encoding handles multi-byte characters correctly
            chunk_string = chunk_bytes.decode('utf-8', errors='ignore')
            chunk_data = f"{command_type} {index} {total_chunks} {chunk_string}"
            
            if not self.send_packet_and_wait_ack('data', chunk_data):
                print(f"Retrying to send chunk {index} for {command_type}")
     else:
           
       if not self.send_packet_and_wait_ack('data', f"{command_type} {data}"):
        print("Failed to send data for", command_type)
        return False

    # End the command
     if not self.send_packet_and_wait_ack('end', f"{command_type} end"):
        print("Failed to end command for", command_type)
        return False

     return True


    def handle_message(self,command, msg_data):
        if(command=='msg'):
          self.send_command('msg', msg_data)
        elif (command =='list'):
           self.send_command(msg_data)
        elif (command =='quit'):
            self.send_command(msg_data)
        #    print("List sent to user")
        else:
         print("Failed to send message.")

    def receive_handler(self):
        while not self.stop:
            try:
                message, _ = self.sock.recvfrom(1500)
                packet_type, seq_num, data, checksum = parse_packet(message.decode('utf-8'))
                parts = data.split(' ', 2)
                msg_type = parts[0]
                if packet_type == 'ack' and int(seq_num) == self.seq_num+1:
                    with self.lock:
                        self.ack_received[self.seq_num] = True
                        self.ack_event.set()  # Signal that ACK has been received
                       
               
                elif msg_type in ['forward_message', 'response_users_list']:
                 
                    if msg_type == 'forward_message':
                        sender = parts[1].rstrip(':')
                        message_content = parts[2]
                        print(f"msg: {sender}: {message_content}")
                        self.send_ack_to_server(self.seq_num)
                    elif msg_type == 'response_users_list':
                        print(f"list: {parts[2]}")
                        self.send_ack_to_server(self.seq_num)
                    elif msg_type == 'ERR_SERVER_FULL':
                       print("disconnected: server full")
                       break
                    elif msg_type == 'ERR_USERNAME_UNAVAILABLE':
                      print("disconnected: username not available")
                      break
                        

                # Send ACK to server after processing message
                    self.send_ack_to_server(self.seq_num)


            except socket.timeout:
                continue  
    def send_ack_to_server(self, seq_num):
     ack_packet = make_packet('ack', int(seq_num), '')
     self.sock.sendto(ack_packet.encode('utf-8'), (self.server_addr, self.server_port))



    def send_packet_and_wait_ack(self, packet_type, data):
     packet = make_packet(packet_type, self.seq_num, data)
     self.sock.sendto(packet.encode('utf-8'), (self.server_addr, self.server_port))
     self.ack_event.clear()  # Reset the event before waiting
     self.ack_event.wait(0.5) 

     if self.ack_received.get(self.seq_num):
        self.seq_num += 1  # Increment sequence number after successful ACK
        return True
     return False


    def join_chat(self):
        # print("Joining chat...")
        return self.send_packet_and_wait_ack('start', f"join {self.name}") and \
               self.send_packet_and_wait_ack('data', f"join {self.name}") and \
               self.send_packet_and_wait_ack('end', '')

    def send_data(self, data):
        # print("Sending data here")
        return self.send_packet_and_wait_ack('data', data)

    def send_end(self):
        # print("Ending packet here")
        return self.send_packet_and_wait_ack('end', '')



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
