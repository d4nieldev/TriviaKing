import constants as c
import socket
import random
import struct
import threading
import select
import sys
try:
    import msvcrt
except ImportError:
    # on mac
    pass

BOT_USED_NUMBERS = set()  # Keep track of used bot numbers
TEAM_USED_NAMES = set()  # Hard-coded list of team names, randomlly picked by Client app

class Client:
    def __init__(self, bot=False):
        self.server_port = None
        self.BUFFER_SIZE = 1024  # Assuming a buffer size value
        self.team_name = self.generate_bot_name() if bot else self.generate_team_name()
        self.BROADCAST_MSG = f'me llamo {self.team_name} and I want to play, pandejo!'
        self.tcp_socket = None
        self.server_ip = None
        self.server_name = None
        self.bot = bot
        self.server_messages = []
        self.server_messages_pending_condition = threading.Condition()
        self.received_new_message = threading.Event()

        # States: looking_for_server, connecting_to_server, game_mode
        self.state = c.CLIENT_STATE_LOOKING_FOR_SERVER
        
        # Input recieved by manual player
        self.answer = None

    @classmethod
    def generate_bot_name(cls):
        while True:
            random_number = random.randint(1, 99999999999)  # Generate a random number
            if random_number not in BOT_USED_NUMBERS:
                BOT_USED_NUMBERS.add(random_number)  # Mark this number as used
                # Return the unique bot team name
                return f"BOT_#{random_number}"
    
    @classmethod
    def generate_team_name(cls):
        while True:
            random_name = random.choice(c.CLIENT_TEAM_NAMES)  # Generate a random name
            if random_name not in TEAM_USED_NAMES:
                TEAM_USED_NAMES.add(random_name)  # Mark this number as used
                # Return the unique bot team name
                return random_name

    def answer_the_bloody_question(self):        
        if self.bot:
            # Random answer can be replaced with any chatbot API, but we are poor
            ans = random.choice(c.TRUE_ANSWERS + c.FALSE_ANSWERS)
            print(f"{self.team_name} Answer: {ans}")
        else:
            ans = self.wait_for_input()
            print(f"Answer: {ans}")
        return ans

    def transition_state(self, new_state):
        self.state = new_state
        print(f"{self.team_name} transitioned to state: {new_state}")

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
            raise ValueError(f"Invalid packet received by {self.team_name}")

        return server_name, server_port

    def find_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
            try:
                # Different commands between MAC and Windows
                udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except AttributeError:
                udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Bind to the broadcast port
            udp_socket.bind(('', c.BROADCAST_PORT))
            try:
                print(f"{self.team_name} is listening for server broadcasts...")
                data, addr = udp_socket.recvfrom(self.BUFFER_SIZE)
                self.server_ip = addr[0]
                
                self.server_name,  self.server_port = self.parse_broadcast_message(data)

                print(f"{self.team_name} Received broadcast from {addr},"
                      f" server name {self.server_name}")
                self.transition_state(c.CLIENT_STATE_CONNECTING_TO_SERVER)

            except socket.timeout:
                print(f"{c.COLOR_RED}[{self.team_name}]: No server broadcasts received.{c.COLOR_RESET}")

    def connect_to_server(self):
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.tcp_socket.connect((self.server_ip, self.server_port))
            self.tcp_socket.send((self.team_name + '\n').encode())
            print(f"{self.team_name} connected to the server and sent player name.")
            self.transition_state(c.CLIENT_STATE_GAME_MODE)
        except Exception as e:
            print(f"{c.COLOR_RED}Failed to connect: {e}{c.COLOR_RESET}")
            self.disconnect()

    def listen_to_server(self):
        while True:
            try:
                data = self.tcp_socket.recv(self.BUFFER_SIZE)
                if data == 0:
                    self.disconnect()
                self.received_new_message.set()
                with self.server_messages_pending_condition:
                    self.server_messages += data.decode().split(c.SERVER_MSG_TERMINATION)
                    self.server_messages_pending_condition.notify()
            except ConnectionAbortedError:
                self.reconnect()
                break
            except OSError:
                break

    # def wait_for_input(self):
    #     self.received_new_message.clear()
    #     while not self.received_new_message.is_set():
    #         # Use select to check if there is input available without blocking
    #         input_ready, _, _ = select.select([sys.stdin], [], [], 0.01)
    #         if input_ready:
    #             # Read user input
    #             return sys.stdin.readline().rstrip()
    #     return None
    
    def wait_for_input(self):
        self.received_new_message.clear()
        while not self.received_new_message.is_set():
            try:
                # Use select to check if there is input available without blocking
                input_ready, _, _ = select.select([sys.stdin], [], [], 0.01)
                if input_ready:
                    # Read user input
                    return sys.stdin.readline().rstrip()
            except OSError:
                # Handle the case for Windows when select is used with stdin
                if msvcrt.kbhit():
                    return sys.stdin.readline().rstrip()

        return None

    def game_mode(self):
        last_question = None
        was_error = False

        server_listener_thread = threading.Thread(target=self.listen_to_server)
        server_listener_thread.start()
        while self.state == c.CLIENT_STATE_GAME_MODE:
            if not was_error:
                with self.server_messages_pending_condition:
                    if len(self.server_messages) == 0:
                        self.server_messages_pending_condition.wait()
                    data = self.server_messages.pop(0)
            else:
                data = last_question
                was_error = False

            server_message = data
            if server_message.startswith(c.WELCOME_MESSAGE):
                server_message = server_message.replace(c.WELCOME_MESSAGE, "")
                print(f"{c.COLOR_GREEN}{server_message}{c.COLOR_RESET}")
            elif server_message.startswith(c.ERROR_MESSAGE):
                server_message = server_message.replace(c.ERROR_MESSAGE, "")
                print(f"{c.COLOR_RED}Error: {server_message}{c.COLOR_RESET}")
                server_message = last_question
                was_error = True
            elif server_message.startswith(c.QUESTION_MESSAGE):
                last_question = server_message
                server_message = server_message.replace(c.QUESTION_MESSAGE, "")
                print(f"{c.COLOR_BLUE}Question: {server_message}{c.COLOR_RESET}")
                ans = self.answer_the_bloody_question()
                if ans is not None:
                    self.tcp_socket.sendall(ans.encode())
            elif server_message.startswith(c.GAME_OVER_MESSAGE):
                server_message = server_message.replace(c.GAME_OVER_MESSAGE, "")
                print(f"{c.COLOR_GREEN}{server_message}{c.COLOR_RESET}")
                self.reconnect()
            elif server_message.startswith(c.GENERAL_MESSAGE):
                server_message = server_message.replace(c.GENERAL_MESSAGE, "")
                print(f"{c.COLOR_YELLOW}{server_message}{c.COLOR_RESET}")

    def disconnect(self):
        if self.tcp_socket:
            self.tcp_socket.close()
            print(f"{c.COLOR_RED}{self.team_name} disconnected from server.{c.COLOR_RESET}")
            self.tcp_socket = None
    
    def reconnect(self):
        self.disconnect()
        self.transition_state(c.CLIENT_STATE_LOOKING_FOR_SERVER)

    def run(self):
        while True:
            if self.state == c.CLIENT_STATE_LOOKING_FOR_SERVER:
                self.find_server()
            elif self.state == c.CLIENT_STATE_CONNECTING_TO_SERVER:
                self.connect_to_server()
            elif self.state == c.CLIENT_STATE_GAME_MODE:
                self.game_mode()


def create_player(bot=False):
    '''
    External method to create players, both human and bots, 
    in order to activate as a thread worker if necessary.
    '''
    if bot:
        client = Client(bot=True)
        client.run()
    else:
        client = Client(bot=False)
        print(f"{c.COLOR_BLUE}Your team name is: {client.team_name}{c.COLOR_RESET}")
        client.run()
    return


if __name__ == '__main__':
    while True:
        client_type = input(
            """\nHello comrad!\nPress P if you want to sign in as a player.\nPress B if you want bot players to join the game:\n""").lower().strip()
        if client_type == "b":
            # Random number of bots will join the game
            num_bots = random.randint(c.MIN_NUM_BOTS, c.MAX_NUM_BOTS)
            # num_bots = 2  # Constant number of bots
            threads = []
            for i in range(num_bots):
                thread = threading.Thread(
                    target=create_player, args=[True])
                threads.append(thread)
                thread.start()

            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            break

        elif client_type == "p":
            create_player(bot=False)
            break
        else:
            print(f'{c.COLOR_RED}Invalid player choice. Try better next time.{c.COLOR_RESET}')
