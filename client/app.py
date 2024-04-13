import constants as c
import sys
import socket
import select
import time

class Client:
    def __init__(self):
        self.SERVER_PORT = c.BROADCAST_PORT
        self.BROADCAST_MSG = 'Are there any servers?'
        self.BUFFER_SIZE = c.CLIENT_NAME_PACKET_SIZE
        self.tcp_socket = None
        self.server_ip = None

    def find_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
            udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            udp_socket.sendto(self.BROADCAST_MSG.encode(), ('<broadcast>', self.SERVER_PORT))
            udp_socket.settimeout(5.0)  # Timeout after 5 seconds if no response
            try:
                data, addr = udp_socket.recvfrom(self.BUFFER_SIZE)
                print(f"Server found at {addr}")
                self.server_ip = addr[0]
                return True
            except socket.timeout:
                print("No server found.")
                return False

    def connect_to_server(self):
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.connect((self.server_ip, self.SERVER_PORT))
        print("Connected to the server.")

    def game_mode(self):
        self.tcp_socket.setblocking(0)
        try:
            while True:
                ready_to_read, _, _ = select.select([self.tcp_socket, sys.stdin], [], [])
                for sock in ready_to_read:
                    if sock == self.tcp_socket:
                        data = sock.recv(self.BUFFER_SIZE)
                        if data:
                            print(f"Received: {data.decode()}")
                        else:
                            print("Server disconnected.")
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

    def run_client(self):
        if self.find_server():
            self.connect_to_server()
            self.game_mode()

    def handle(self):
        while True:
            if not self.server_ip:
                if not self.find_server():
                    time.sleep(5)  # Wait and try to find server again
                    continue
            if not self.tcp_socket:
                self.connect_to_server()
            self.game_mode()
            break  # Exit after game mode finishes or disconnects


    def handle_bot():
        # send answer bot
        self.handle()


    def handle_human():
        # send answer human
        self.handle()

if __name__ == '__main__':
    client = Client()
    client.handle()


# if __name__ == "__main__":
#     if len(sys.argv) == 2:
#         if sys.argv[1] == 'bot':
#             # be bot
#             handle_bot()
#     # be human
#     handle_human()
