import constants as c
import socket
import select
import sys
import time
import struct

class Client:
    def __init__(self, team_name="Team 1", bot = False):
        self.SERVER_PORT = None
        self.BROADCAST_MSG = 'I want to play pandejo!'
        self.BUFFER_SIZE = c.CLIENT_NAME_PACKET_SIZE
        self.team_name = team_name
        self.tcp_socket = None
        self.server_ip = None
        self.server_name = None
        self.state = 'looking_for_server'  # States: looking_for_server, connecting_to_server, game_mode
        self.bot = bot

    def transition_state(self, new_state):
        self.state = new_state
        print(f"Transitioned to state: {new_state}")
        
    def parse_broadcast_message(self, data: bytes):
        # Expected format of the received packet
        format_specifier = '>IB32sH'  # Big-endian unsigned int, unsigned byte, 32-byte string, unsigned short
        
        unpacked_data = struct.unpack(format_specifier, data)
        magic_cookie = unpacked_data[0]
        message_type = unpacked_data[1]
        server_name = unpacked_data[2].decode('utf-16le').rstrip('\x00')  # Remove padding
        server_port = unpacked_data[3]
        
        # Verify the magic cookie and message type
        if magic_cookie != c.BROADCAST_MAGIC_COOKIE or message_type != c.BROADCAST_MESSAGE_TYPE:
            raise ValueError("Invalid packet received")
        
        return {
            "server_name": server_name,
            "server_port": server_port
        }


    def find_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
            udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            udp_socket.bind(('', c.BROADCAST_PORT))  # Bind to the broadcast port
            try:
                print("Listening for server broadcasts...")
                data, addr = udp_socket.recvfrom(self.BUFFER_SIZE)
                res = self.parse_broadcast_message(data)
                
                self.server_ip = addr[0]
                self.server_port = res['server_port']
                self.server_name = res['server_name']
                print(f"Received broadcast from {addr}, server name {self.server_name}")
                self.transition_state('connecting_to_server')
                
            except socket.timeout:
                print("No server broadcast received.")

    def connect_to_server(self):
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.tcp_socket.connect((self.server_ip, self.SERVER_PORT))
            self.tcp_socket.send((self.team_name + '\n').encode())
            print("Connected to the server and sent player name.")
            self.transition_state('game_mode')
        except Exception as e:
            print(f"Failed to connect: {e}")
            self.disconnect()

    def game_mode(self):
        self.tcp_socket.setblocking(0)
        try:
            while self.state == 'game_mode':
                ready_to_read, _, _ = select.select([self.tcp_socket, sys.stdin], [], [])
                for sock in ready_to_read:
                    if sock == self.tcp_socket:
                        data = sock.recv(self.BUFFER_SIZE)
                        if data:
                            print(f"Received: {data.decode()}")
                        else:
                            print("Server disconnected.")
                            self.transition_state('looking_for_server')
                            return
                    else:
                        msg = sys.stdin.readline()
                        self.tcp_socket.send(msg.encode())
        finally:
            self.disconnect()

    def disconnect(self):
        if self.tcp_socket:
            self.tcp_socket.close()
            print("Disconnected from server.")
            self.tcp_socket = None

    def run(self):
        while True:
            if self.state == 'looking_for_server':
                self.find_server()
            elif self.state == 'connecting_to_server':
                self.connect_to_server()
            elif self.state == 'game_mode':
                self.game_mode()

if __name__ == '__main__':
    client = Client("Te Quiero Putas")
    client.run()


# def handle_bot():
#     # send answer bot
#     self.handle()
# def handle_human():
#     # send answer human
#     self.handle()
# if __name__ == "__main__":
#     if len(sys.argv) == 2:
#         if sys.argv[1] == 'bot':
#             # be bot
#             handle_bot()
#     # be human
#     handle_human()
