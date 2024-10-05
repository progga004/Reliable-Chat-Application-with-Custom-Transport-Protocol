'''
This module defines the behaviour of server in your Chat Application
'''
import sys
import getopt
import socket
# import util
from util import make_message,MAX_NUM_CLIENTS,make_packet,parse_packet


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
   
    def start(self):
        while True:
            message, client_addr = self.sock.recvfrom(1024)
            packet_type, seq_num, data, checksum = parse_packet(message.decode('utf-8'))
            
            if packet_type == 'data':
                parts = data.split(' ', 2)
               
                msg_type = parts[0]
                if msg_type == 'join':
                    username = parts[1]
                    if len(self.clients) >= MAX_NUM_CLIENTS:
                        response = make_packet('data', 0, "ERR_SERVER_FULL")
                        print("response send",response)
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
                    sender,recipients_and_message = parts[1:]
                    
                    num_users_str, recipients_and_message=recipients_and_message.split(' ', 1)
                   
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
                            print(f"msg: {sender}")
                            print(f"msg: {sender} to non-existent user {recipient}")

                elif msg_type == 'disconnect':
                    username = parts[1]
                    if username in self.clients:
                        del self.clients[username]
                        print(f"disconnected: {username}")
                # if msg_type == 'unknown_command':
                #    username = parts[1]
                #    response = make_packet('data', 0, 'ERR_UNKNOWN_MESSAGE')
                #    self.sock.sendto(response.encode('utf-8'), client_addr)
                #    print(f"disconnected: {username} sent unknown command")
                #    if username in self.clients:
                #         del self.clients[username]
                   
    
    
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
