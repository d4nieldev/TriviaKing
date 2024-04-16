import constants as c
import socket
import random
import struct


class Client:
    def __init__(self, team_name="Team 1", bot=False):
        self.server_port = None
        self.BROADCAST_MSG = 'I want to play pandejo!'
        self.BUFFER_SIZE = 1024  # Assuming a buffer size value
        self.team_name = team_name
        self.tcp_socket = None
        self.server_ip = None
        self.server_name = None
        
        # States: looking_for_server, connecting_to_server, game_mode
        self.state = 'looking_for_server'
        self.bot = bot
        
        if bot:
            self.team_name = self.generate_bot_name()
    
    @classmethod
    def generate_bot_name(cls):
        while True:
            random_number = random.randint(1, 99999999999)  # Generate a random number
            if random_number not in c.BOT_USED_NUMBERS:
                c.BOT_USED_NUMBERS.add(random_number)  # Mark this number as used
                return f"BOT_#{random_number}"  # Return the unique bot team name
    
    def answer_the_bloody_question(self):
        if self.bot:
            # Random answer can be replaced with any chatbot API, but we are poor
            ans = random.choice(list(c.TRUE_ANSWERS.union(c.FALSE_ANSWERS)))
        else:
            ans = input("Answer: ").strip()
        return ans
            

    def transition_state(self, new_state):
        self.state = new_state
        print(f"Transitioned to state: {new_state}")

    def parse_broadcast_message(self, data: bytes):
        # Expected format of the received packet
        # Big-endian unsigned int, unsigned byte, 32-byte string, unsigned short
        format_specifier = '>IB32sH'

        unpacked_data = struct.unpack(format_specifier, data)
        magic_cookie = unpacked_data[0]
        message_type = unpacked_data[1]
        server_name = unpacked_data[2].decode(
            'utf-16le').rstrip('\x00')  # Remove padding
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
            # Bind to the broadcast port
            udp_socket.bind(('', c.BROADCAST_PORT))
            try:
                print("Listening for server broadcasts...")
                data, addr = udp_socket.recvfrom(self.BUFFER_SIZE)
                res = self.parse_broadcast_message(data)

                self.server_ip = addr[0]
                self.server_port = res['server_port']
                self.server_name = res['server_name']
                print(f"Received broadcast from {addr},"
                      f" server name {self.server_name}")
                self.transition_state('connecting_to_server')

            except socket.timeout:
                print("No server broadcast received.")

    def connect_to_server(self):
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.tcp_socket.connect((self.server_ip, self.server_port))
            self.tcp_socket.send((self.team_name + '\n').encode())
            print("Connected to the server and sent player name.")
            self.transition_state('game_mode')
        except Exception as e:
            print(f"Failed to connect: {e}")
            self.disconnect()

    def game_mode(self):
        try:
            last_question = None
            was_error = False
            while self.state == 'game_mode':
                if not was_error:
                    data = self.tcp_socket.recv(self.BUFFER_SIZE)
                else:
                    data = last_question.encode()
                    was_error = False

                if data == 0:
                    print("Server disconnected.")
                    self.transition_state('looking_for_server')
                    return

                server_message = data.decode()
                if server_message.startswith(c.WELCOME_MESSAGE):
                    server_message = server_message.replace(
                        c.WELCOME_MESSAGE, "")
                    print(server_message)
                elif server_message.startswith(c.ERROR_MESSAGE):
                    server_message = server_message.replace(
                        c.ERROR_MESSAGE, "")
                    print("Error: " + server_message)
                    server_message = last_question
                    was_error = True
                elif server_message.startswith(c.QUESTION_MESSAGE):
                    last_question = server_message
                    server_message = server_message.replace(
                        c.QUESTION_MESSAGE, "")
                    print(f"{c.COLOR_BLUE}Question: {server_message}{c.COLOR_RESET}")
                    msg = self.answer_the_bloody_question()
                    self.tcp_socket.sendall(msg.encode())
                elif server_message.startswith(c.BYE_MESSAGE):
                    server_message = server_message.replace(
                        c.BYE_MESSAGE, "")
                    print(f"{c.COLOR_RED}{server_message}{c.COLOR_RESET}")
                elif server_message.startswith(c.GAME_OVER_MESSAGE):
                    server_message = server_message.replace(
                        c.GAME_OVER_MESSAGE, "")
                    print(f"{c.COLOR_BLUE}{server_message}{c.COLOR_RESET}")
                    self.transition_state('looking_for_server')
                    return

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
    while True:
        client_type = input("""Hello comrad! Press P if you want to sign in as a player. 
                            Press B if you want a bot player to join the game""").lower().strip()
        if client_type == "b":
            client = Client(bot=True)
            client.run()
            break
        elif client_type == "p":
            team_name = input("Enter player name: ").strip()
            client = Client(team_name=team_name, bot=False)
            client.run()
            break
        else:
            print('Invalid player choice. Try better next time.')
