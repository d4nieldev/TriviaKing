import constants as c
from questions import QUESTIONS_DICT
import socket
import random
import struct
import threading
import select
import sys
try:
    import msvcrt
except ImportError:
    # on MAC
    pass

PRINT_LOCK = threading.Lock()
RECONNECT_LOCK = threading.Lock()
BOT_USED_NUMBERS = set()  # Keep track of used bot numbers
TEAM_USED_NAMES = set()  # Hard-coded list of team names, randomlly picked by Client app

def safe_print(*args, **kwargs):
    '''
    Makes sure that prints to screen are handeled properly when received from 
    multiple threads.
    '''
    with PRINT_LOCK:
        print(*args, **kwargs)


class Client:
    def __init__(self, bot=False, bot_level = None):
        self.server_port = None
        self.BUFFER_SIZE = 1024  # Assuming a buffer size value
        self.team_name = self.generate_bot_name() if bot else self.generate_team_name()
        self.BROADCAST_MSG = f'me llamo {self.team_name} and I want to play, pandejo!'
        self.tcp_socket = None
        self.server_ip = None
        self.server_name = None
        self.connected = False
        self.bot = bot
        self.bot_level = bot_level
        self.server_messages = []
        self.server_messages_pending_condition = threading.Condition()
        self.received_new_message = threading.Event()
        self.state = c.CLIENT_STATE_LOOKING_FOR_SERVER  # States: looking_for_server, connecting_to_server, game_mode
        self.answer = None # Input recieved by manual player
        self.curr_question = None  # Current question in game


    @classmethod
    def generate_bot_name(cls):
        '''
        Automatically generate a valid bot name using a set prefix "BOT_#..."
        and a random number assignment.
        2 bot names will not be the same (under the same server), as the numbers
        are monitored in a class variable.
        '''
        while True:
            random_number = random.randint(c.MIN_BOT_ID, c.MAX_BOT_ID)  # Generate a random number
            if random_number not in BOT_USED_NUMBERS:
                BOT_USED_NUMBERS.add(random_number)  # Mark this number as used
                # Return the unique bot team name
                return c.BOT_NAME_FORMAT.format(id=random_number)

    
    @classmethod
    def generate_team_name(cls):
        '''
        Automatically generate a team name from a const list of names.
        2 player names will not be the same (under the same server), as the active names
        are monitored in a class variable.
        '''
        while True:
            random_name = random.choice(c.CLIENT_TEAM_NAMES)  # Generate a random name
            if random_name not in TEAM_USED_NAMES:
                TEAM_USED_NAMES.add(random_name)  # Mark this number as used
                # Return the unique bot team name
                return random_name


    def answer_the_bloody_question(self):
        '''
        Handle answering the question.
        For Bots:
        Depending on the bot level, as a probability of choosing the right answer,
        return an answer to the current question, saved as a class variable. Answer is returned
        directly from questions.py file.
        For human clients:
        Activate input thread while waiting for the client to enter an answer in 
        wait_for_input()
        
        Return client / bot answer or None, if no valid answer was given.
        '''
        if self.bot:
            # Get the correct answer for the current question from the dictionary
            correct_ans = QUESTIONS_DICT[self.curr_question]
            # Decide whether to answer correctly based on the bot's level
            if random.random() < self.bot_level:
                ans = correct_ans
            else:
                ans = not correct_ans
            # Map Boolean answer to string
            ans = c.TRUE_ANSWERS[1] if ans else c.FALSE_ANSWERS[1]
            safe_print(f"Answer: {ans}")
        else:
            ans = self.wait_for_input()
        if ans is not None and len(ans) > 1:
            safe_print(f"{c.COLOR_RED}Answer exeeded answer length, sending '{ans[0]}'{c.COLOR_RESET}")
        return ans[0] if ans else None


    def transition_state(self, new_state):
        '''
        Change client's state without giving the activator of the function direct
        access to class attributes.
        '''
        safe_print(f"{self.team_name} transitioned from state {self.state} to state: {new_state}")
        self.state = new_state


    def parse_broadcast_message(self, data: bytes):
        '''
        Parse the message received from the server, while verifying it's structure.
        Extract server name and port from message
        '''
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
        '''
        Look for an available game server using a UDP connection.
        Function can handle connections both on Windows and Mac computers.
        '''
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
            try:
                # Different commands between MAC and Windows
                udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except AttributeError:
                udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Bind to the broadcast port
            udp_socket.bind(('', c.BROADCAST_PORT))
            try:
                safe_print(f"{self.team_name} is listening for server broadcasts...")
                data, addr = udp_socket.recvfrom(self.BUFFER_SIZE)
                self.server_ip = addr[0]
                
                self.server_name,  self.server_port = self.parse_broadcast_message(data)

                safe_print(f"{self.team_name} Received broadcast from {addr},"
                      f" server name {self.server_name}")
                self.transition_state(c.CLIENT_STATE_CONNECTING_TO_SERVER)

            except socket.timeout:
                safe_print(f"{c.COLOR_RED}[{self.team_name}]: No server broadcasts received.{c.COLOR_RESET}")

    def connect_to_server(self):
        '''
        Establish a TCP connection with the found game server and send the team name
        '''
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.tcp_socket.connect((self.server_ip, self.server_port))
            self.tcp_socket.send((self.team_name + c.CLIENT_NAME_TERMINATION).encode())
            self.connected = True
            safe_print(f"{self.team_name} connected to the server and sent player name.")
            self.transition_state(c.CLIENT_STATE_GAME_MODE)
        except Exception as e:
            safe_print(f"{c.COLOR_RED}Failed to connect: {e}{c.COLOR_RESET}")
            
            # Connecion failed, allow client to look for other servers
            self.reconnect()
            

    def listen_to_server(self):
        '''
        Receive messages via TCP connection from server to client.
        '''
        while True:
            try:
                if self.tcp_socket is None:
                    safe_print(f'{c.COLOR_RED}No connection to the server. Attempting to reconnect...{c.COLOR_RESET}')
                    self.reconnect()
                    break  # Stop listening to server, look for another connection and restart
                
                data = self.tcp_socket.recv(self.BUFFER_SIZE)
                if not data:
                    safe_print(f'{c.COLOR_RED}server disconnected. reconnecting...{c.COLOR_RESET}')
                    self.reconnect()
                    break # Stop listening to server (disconnected), look for another connection and restart
                self.received_new_message.set()
                new_server_messages = data.decode().split(c.SERVER_MSG_TERMINATION)
                new_server_messages = [msg for msg in new_server_messages if len(msg) > 0]
                with self.server_messages_pending_condition:
                    self.server_messages += new_server_messages
                    self.server_messages_pending_condition.notify()
            except (ConnectionAbortedError, OSError) as e:
                self.reconnect()
                break
            
        # We exited the loop for error / game over, etc...
        # Notify main thread that server disconnected - Free it
        with self.server_messages_pending_condition:
            self.server_messages_pending_condition.notify()
            
    
    def wait_for_input(self):
        '''
        Recieve user input in thread while not blocking incoming server messages
        '''
        self.received_new_message.clear()
        ans = None
        safe_print("Answer: ", end='', flush=True)
        while not self.received_new_message.is_set():
            try:
                # Use select to check if there is input available without blocking
                input_ready, _, _ = select.select([sys.stdin], [], [], c.CLIENT_INPUT_REFRESH_SEC)
                if input_ready:
                    # Read user input
                    ans = sys.stdin.readline().rstrip()
                    break
            except OSError:
                # Handle the case for Windows when select is used with stdin
                if msvcrt.kbhit():
                    ans = sys.stdin.readline().rstrip()
                    break
        return ans


    def game_mode(self):
        '''
        Manage game communication on client side
        1. Get server messages from queue
        2. Identify message type (welcome, error, question...)
        3. Parse message content properly
        4. Handle.
        '''
        self.curr_question = None
        was_error = False

        server_listener_thread = threading.Thread(target=self.listen_to_server)
        server_listener_thread.start()
        while self.state == c.CLIENT_STATE_GAME_MODE:
            if not was_error:
                with self.server_messages_pending_condition:
                    if len(self.server_messages) == 0:
                        self.server_messages_pending_condition.wait()
                    if not self.connected:
                        break

                    server_message = self.server_messages.pop(0)
            else:
                server_message = c.QUESTION_MESSAGE + self.curr_question
                was_error = False

            if server_message.startswith(c.WELCOME_MESSAGE):
                server_message = server_message.replace(c.WELCOME_MESSAGE, "")
                safe_print(f"{c.COLOR_GREEN}{server_message}{c.COLOR_RESET}")
            elif server_message.startswith(c.ERROR_MESSAGE):
                server_message = server_message.replace(c.ERROR_MESSAGE, "")
                safe_print(f"{c.COLOR_RED}Error: {server_message}{c.COLOR_RESET}")
                was_error = True
            elif server_message.startswith(c.QUESTION_MESSAGE):
                server_message = server_message.replace(c.QUESTION_MESSAGE, "")
                self.curr_question = server_message
                safe_print(f"{c.COLOR_BLUE}Question: {server_message}{c.COLOR_RESET}")
                ans = self.answer_the_bloody_question()
                if ans is not None:
                    self.tcp_socket.sendall(ans.encode())
            elif server_message.startswith(c.GAME_OVER_MESSAGE):
                server_message = server_message.replace(c.GAME_OVER_MESSAGE, "")
                safe_print(f"{c.COLOR_GREEN}{server_message}{c.COLOR_RESET}")
                self.reconnect()  # Will change state => exit loop
            elif server_message.startswith(c.GENERAL_MESSAGE):
                server_message = server_message.replace(c.GENERAL_MESSAGE, "")
                safe_print(f"{c.COLOR_YELLOW}{server_message}{c.COLOR_RESET}")
                

    def disconnect(self):
        '''
        Close TCP connection with server
        '''
        self.tcp_socket.close()
        safe_print(f"{c.COLOR_RED}{self.team_name} disconnected from server.{c.COLOR_RESET}")
        self.tcp_socket = None
        self.connected = False

    
    def reconnect(self):
        '''
        Close connection with current server and open player to look for other 
        available servers.
        Use RECONNECT_LOCK to ensure reconnect function is not being called twice
        '''
        with RECONNECT_LOCK:
            if self.tcp_socket:
                self.disconnect()
                _ = input(f"{c.COLOR_YELLOW}Press Enter if you wish {self.team_name} to reconnect to the game server{c.COLOR_RESET}")
                
            if self.state != c.CLIENT_STATE_LOOKING_FOR_SERVER:
                self.transition_state(c.CLIENT_STATE_LOOKING_FOR_SERVER)


    def run(self):
        '''
        Handle the 3 client statets
        1. Looking for server
        2. Found server, connect
        3. Game
        '''
        while True:            
            if self.state == c.CLIENT_STATE_LOOKING_FOR_SERVER:
                self.find_server()
            elif self.state == c.CLIENT_STATE_CONNECTING_TO_SERVER:
                self.connect_to_server()
            elif self.state == c.CLIENT_STATE_GAME_MODE:
                self.game_mode()


def create_player(bot=False, bot_level_str='c'):
    '''
    External method from class to create players (class instances), both human and bots.
    Bots are created in threads, so an external worker function like this is needed.
    '''
    if bot:
        client = Client(bot=True, bot_level=c.BOT_LEVELS[bot_level_str])
        
    else:
        client = Client(bot=False)
        safe_print(f"{c.COLOR_BLUE}Your team name is: {client.team_name}{c.COLOR_RESET}")
    
    client.run()



if __name__ == '__main__':
    while True:
        client_type = input(
            """\nHello comrad!\nPress P if you want to sign in as a player.\nPress B if you want bot players to join the game:\n""").lower().strip()
        if client_type == c.BOT_TYPE:
            while True:
                try:
                    num_bots = int(input("""How many bots would you like to add to the game?\n""").lower().strip())
                    if num_bots == 0:
                        raise Exception("Number of bost needs to be greater than 0.")
                    break
                except Exception:
                    safe_print(f'{c.COLOR_RED}Invalid player choice. Try better next time.{c.COLOR_RESET}')

            while True:
                bot_level_str = input("""\nHow smart would you like the bot to be?\nPress 'A' for Sheldon Cooper smart\nPress 'B' for Brainy Smurf smart\nPress 'C' for average US public school smart\nPress 'D' for Dumb as Fu*k\n""").lower().strip()
                if bot_level_str not in c.BOT_LEVELS.keys():
                    safe_print(f'{c.COLOR_RED}Invalid player choice. Try better next time.{c.COLOR_RESET}')
                    continue
                break
            threads = []
            for i in range(num_bots):
                thread = threading.Thread(
                    target=create_player, args=[True, bot_level_str])
                threads.append(thread)
                thread.start()

            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            break

        elif client_type == c.PLAYER_TYPE:
            create_player(bot=False)
            break
        else:
            safe_print(f'{c.COLOR_RED}Invalid player choice. Try better next time.{c.COLOR_RESET}')
