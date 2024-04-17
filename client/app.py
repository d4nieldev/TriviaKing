import constants as c
import socket
import random
import struct
import threading

BOT_USED_NUMBERS = set()  # Keep track of used bot numbers


class Client:
    def __init__(self, team_name="Team 1", bot=False):
        self.server_port = None
        self.BUFFER_SIZE = 1024  # Assuming a buffer size value
        self.team_name = self.generate_bot_name() if bot else team_name
        self.BROADCAST_MSG = f'me llamo {self.team_name} and I want to play, pandejo!'
        self.tcp_socket = None
        self.server_ip = None
        self.server_name = None
        self.bot = bot

        # States: looking_for_server, connecting_to_server, game_mode
        self.state = 'looking_for_server'

    @classmethod
    def generate_bot_name(cls):
        while True:
            random_number = random.randint(
                1, 99999999999)  # Generate a random number
            if random_number not in BOT_USED_NUMBERS:
                BOT_USED_NUMBERS.add(random_number)  # Mark this number as used
                # Return the unique bot team name
                return f"BOT_#{random_number}"

    def answer_the_bloody_question(self):
        if self.bot:
            # Random answer can be replaced with any chatbot API, but we are poor
            ans = random.choice(c.TRUE_ANSWERS + c.FALSE_ANSWERS)
            print(f"{self.team_name} Answer: {ans}")
        else:
            # input_thread.start()
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
            print(f"{c.COLOR_RED}Failed to connect: {e}{c.COLOR_RESET}")
            self.disconnect()

    def game_mode(self):
        last_question = None
        was_error = False
        while self.state == 'game_mode':
            if not was_error:
                try:
                    data = self.tcp_socket.recv(self.BUFFER_SIZE)
                    # input_thread.stop
                except ConnectionAbortedError:
                    self.reconnect()
            else:
                data = last_question.encode()
                was_error = False

            if data == 0:
                self.disconnect()

            server_message = data.decode()
            if server_message.startswith(c.WELCOME_MESSAGE):
                server_message = server_message.replace(
                    c.WELCOME_MESSAGE, "")
                print(f"{c.COLOR_GREEN}server_message{c.COLOR_RESET}")
            elif server_message.startswith(c.ERROR_MESSAGE):
                server_message = server_message.replace(
                    c.ERROR_MESSAGE, "")
                print(f"{c.COLOR_RED}Error: {server_message}{c.COLOR_RESET}")
                server_message = last_question
                was_error = True
            elif server_message.startswith(c.QUESTION_MESSAGE):
                last_question = server_message
                server_message = server_message.replace(
                    c.QUESTION_MESSAGE, "")
                print(f"{c.COLOR_BLUE}Question: {server_message}{c.COLOR_RESET}")
                msg = self.answer_the_bloody_question()
                self.tcp_socket.sendall(msg.encode())
            elif server_message.startswith(c.GAME_OVER_MESSAGE):
                server_message = server_message.replace(
                    c.GAME_OVER_MESSAGE, "")
                print(f"{c.COLOR_GREEN}{server_message}{c.COLOR_RESET}")
                self.reconnect()
                return

    def disconnect(self):
        if self.tcp_socket:
            self.tcp_socket.close()
            print(f"{c.COLOR_RED}Disconnected from server.{c.COLOR_RESET}")
            self.tcp_socket = None
    
    def reconnect(self):
        self.disconnect()
        self.transition_state(f'{c.COLOR_BLUE}looking_for_server{c.COLOR_RESET}')

    def run(self):
        while True:
            if self.state == 'looking_for_server':
                self.find_server()
            elif self.state == 'connecting_to_server':
                self.connect_to_server()
            elif self.state == 'game_mode':
                self.game_mode()


def create_player(team_name="", bot=False):
    '''
    External method to create players, both human and bots, 
    in order to activate as a thread worker if necessary.
    '''
    if bot:
        client = Client(bot=True)
        client.run()
    else:
        client = Client(team_name=team_name, bot=False)
        client.run()
    return


if __name__ == '__main__':
    while True:
        client_type = input(
            """\nHello comrad!\nPress P if you want to sign in as a player.\nPress B if you want a bot player to join the game:\n""").lower().strip()
        if client_type == "b":
            # Random number of bots will join the game
            num_bots = random.randint(1, 7)
            # num_bots = 2  # Constant number of bots
            threads = []
            for i in range(num_bots):
                thread = threading.Thread(
                    target=create_player, args=("", True))
                threads.append(thread)
                thread.start()

            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            break

        elif client_type == "p":
            team_name = input(f"{c.COLOR_BLUE}Enter player name: {c.COLOR_RESET}").strip()
            create_player(team_name=team_name, bot=False)
            break
        else:
            print(f'{c.COLOR_RED}Invalid player choice. Try better next time.{c.COLOR_RESET}')
