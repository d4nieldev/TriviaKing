import socket
import threading
import struct
import time
import random
import select
from collections import Counter

from questions import QUESTIONS
import constants as c
import statistic as stats


GAME_RUNNING: bool = False
SENT_QUESTION_CONDITION: threading.Condition = threading.Condition()
SENT_QUESTION: bool = False
WAIT_FOR_ANSWERS_CONDITION: threading.Condition = threading.Condition()
ANSWERS_CHECKED_CONDITION: threading.Condition = threading.Condition()
ANSWERS_CHECKED: bool = False

# init the class stats
server_stats = stats.Statistic()

class ClientHandler:
    def __init__(self, client_socket: socket.socket):
        self.socket: socket.socket = client_socket
        self.name: str = None
        self.reset_state()

    def recieve_name(self):
        # get client name
        message = self.socket.recv(c.CLIENT_NAME_PACKET_SIZE).decode()
        self.name = message.split(c.CLIENT_NAME_TERMINATION)[0]
        print(f"{self.name} connected!")

    def reset_state(self):
        self.thread: threading.Thread = threading.Thread(target=self.handle)
        self.answer: bool = None
        self.answered: bool = False
        self.correct: bool = None
        self.in_game: bool = True
        
    def start(self):
        self.reset_state()
        self.thread.start()

    def join(self):
        self.thread.join()

    def disqualify(self):
        self.in_game = False
        self.send_message(c.GENERAL_MESSAGE, "You are not the shapest pencil in the case, try better in the next game!")

    def disconnect(self):
        with CLIENTS_HANDLERS_LOCK:
            if self in CLIENTS_HANDLERS:
                self.socket.close()
                print(f"{c.COLOR_RED}{self.name} disconnected.{c.COLOR_RESET}")
                CLIENTS_HANDLERS.remove(self)
                self.in_game = False
                with WAIT_FOR_ANSWERS_CONDITION:
                    WAIT_FOR_ANSWERS_CONDITION.notify()
    
    def send_message(self, message_type: str, message: str) -> None:
        message = message_type + message + c.SERVER_MSG_TERMINATION
        try:
            self.socket.sendall(message.encode())
        except BrokenPipeError:
            self.disconnect()

    def handle(self):
        self.in_game = True

        while self.in_game and GAME_RUNNING:
            # get answer from client
            answer = None
            with SENT_QUESTION_CONDITION:
                if not SENT_QUESTION:
                    SENT_QUESTION_CONDITION.wait()

            while answer not in c.TRUE_ANSWERS + c.FALSE_ANSWERS:
                try:
                    print(f'waiting for answer from {self.name}')
                    response_ready, _, _ = select.select([self.socket], [], [], c.SERVER_NO_ANSWER_TIMEOUT_SEC)
                    if response_ready:
                        print(f'Waiting for {self.name} input')
                        response = self.socket.recv(c.CLIENT_ANSWER_PACKET_SIZE)
                        print(f"Got response from {self.name}: {response}")
                    else:
                        # did not get response from client
                        print(f"{self.name} did not answer in time.")
                        response = None
                        break
                except Exception:
                    print(f"Error while recieving answer from client {self.name}")
                    self.disconnect()
                    return  # kill the thread
                if response == 0:
                    print(f"{self.name} disconnected.")
                    self.disconnect()
                    return  # kill the thread
                
                answer = response.decode()
                if answer not in c.TRUE_ANSWERS + c.FALSE_ANSWERS:
                    error_message = f"Invalid answer: {answer}"
                    self.send_message(c.ERROR_MESSAGE, error_message)

            if answer in c.TRUE_ANSWERS:
                self.answer = True
            elif answer in c.FALSE_ANSWERS:
                self.answer = False
            else:
                self.answer = None
            self.answered = True

            # nofify the main thread that another player answered
            with WAIT_FOR_ANSWERS_CONDITION:
                WAIT_FOR_ANSWERS_CONDITION.notify()
    

            # wait for all answers to be checked
            with ANSWERS_CHECKED_CONDITION:
                if not ANSWERS_CHECKED:
                    ANSWERS_CHECKED_CONDITION.wait()

            if self.correct is False:
                break

            # reset answer and correct fields
            self.answered = False
            self.answer = None
            self.correct = None


SEND_BROADCAST: bool = False
CLIENTS_HANDLERS: list[ClientHandler] = []
CLIENTS_HANDLERS_LOCK: threading.Lock = threading.Lock()


def get_ip_address() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Connect to any IP (here we choose Google's public DNS server)
        s.connect(('8.8.8.8', 80))
        ip_address = s.getsockname()[0]
    finally:
        s.close()
    return ip_address


def create_broadcast_packet(server_name: str, server_port: int) -> bytes:
    # Constructing the message with the specified format
    magic_cookie = struct.pack('>I', c.BROADCAST_MAGIC_COOKIE)
    message_type = struct.pack('B', c.BROADCAST_MESSAGE_TYPE)
    # Encoding the server name to Unicode and padding it to 32 characters
    encoded_server_name = server_name.encode(
        'utf-16le').ljust(64, b'\x00')[:32]
    # Converting the server port to bytes (big-endian)
    server_port_bytes = struct.pack('>H', server_port)

    # Constructing the UDP packet
    udp_packet = b''.join(
        [magic_cookie, message_type, encoded_server_name, server_port_bytes])
    return udp_packet


def broadcast_loop(ip_address: str, server_name: str, server_port: int) -> None:
    # Creating the UDP packet
    udp_packet = create_broadcast_packet(server_name=server_name,
                                         server_port=server_port)

    broadcast_address = (c.BROADCAST_ADDRESS, c.BROADCAST_PORT)

    print("Server sending offers...")

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        try:
            sock.bind((ip_address, c.BROADCAST_PORT))
        except OSError:
            # on mac
            pass
        while SEND_BROADCAST:
            sock.sendto(udp_packet, broadcast_address)
            time.sleep(c.SERVER_BROADCAST_PERIOD_SEC)


def handle_new_connection(client_socket: socket.socket, client_address: tuple) -> None:
    print("New connection from ", client_address)
    handler: ClientHandler = ClientHandler(client_socket=client_socket)
    CLIENTS_HANDLERS.append(handler)


def handle_incoming_connections(server_socket: socket.socket) -> None:
    # Accept incoming connections
    while True:
        try:
            (client_socket, client_address) = server_socket.accept()
            handle_new_connection(client_socket, client_address)
        except socket.timeout:
            print("Stopped listening for new connections.")
            break


def send_welcome_message() -> None:
    # recieve names from all clients
    for ch in CLIENTS_HANDLERS:
        ch.recieve_name()
        
    welcome_message = f'Welcome to {c.SERVER_NAME} trivia king!\n'
    for i, ch in enumerate(CLIENTS_HANDLERS):
        welcome_message += f'Player {i + 1}: {ch.name}\n'
    welcome_message += '==\n'

    # send welcome message to every player
    for ch in CLIENTS_HANDLERS:
        msg = f"Hello, comrad {ch.name}!\n"
        msg += welcome_message
        ch.send_message(c.WELCOME_MESSAGE, msg)

def get_in_game_players() -> list[ClientHandler]:
    return [ch for ch in CLIENTS_HANDLERS if ch.in_game]


def game_loop() -> ClientHandler:
    global GAME_RUNNING
    global SENT_QUESTION
    global ANSWERS_CHECKED

    SENT_QUESTION = False
    ANSWERS_CHECKED = False

    round_num = 1

    def get_round_start_message() -> str:
        return f"Round {round_num} is starting in {c.ROUND_PAUSE_SEC} seconds. Get ready..."

    GAME_RUNNING = True

    for ch in CLIENTS_HANDLERS:
        ch.start()

    selected_questions_indices = [-1]
    while len(get_in_game_players()) > 1:
        # start the round
        round_start_message = get_round_start_message()
        for ch in CLIENTS_HANDLERS:
            ch.send_message(c.GENERAL_MESSAGE, round_start_message)
        print(f"{c.COLOR_YELLOW}{round_start_message}{c.COLOR_RESET}")
        

        in_game_players_str = ', '.join([p.name for p in get_in_game_players()])
        before_question_message = f"Players still in the game: {in_game_players_str}"
        for ch in CLIENTS_HANDLERS:
            ch.send_message(c.GENERAL_MESSAGE, before_question_message)
        print(f"{c.COLOR_YELLOW}{before_question_message}{c.COLOR_RESET}")

        # optinal - sleep to give players time to prepare
        time.sleep(c.ROUND_PAUSE_SEC)

        # choose a random question
        question_index = -1
        while question_index in selected_questions_indices:
            question_index = random.randint(0, len(QUESTIONS) - 1)
        selected_questions_indices.append(question_index)
        question, answer = QUESTIONS[question_index]
        
        # send the question to all players
        for client_handler in get_in_game_players():
            client_handler.send_message(c.QUESTION_MESSAGE, question)

        with SENT_QUESTION_CONDITION:
            SENT_QUESTION = True
            ANSWERS_CHECKED = False
            SENT_QUESTION_CONDITION.notify_all()

        print(f"{c.COLOR_BLUE}Sent question: {question} (answer: {answer}){c.COLOR_RESET}")

        # wait for answers
        with WAIT_FOR_ANSWERS_CONDITION:
            pending_clients = get_in_game_players()
            while len(get_in_game_players()) > 1 and len(pending_clients) > 0:
                WAIT_FOR_ANSWERS_CONDITION.wait()
                pending_clients = [ch for ch in get_in_game_players() if not ch.answered]
        

        # check answers
        if len(get_in_game_players()) > 1:
            correct_players: list[ClientHandler] = []
            incorrect_players: list[ClientHandler] = []
            for client_handler in get_in_game_players():
                if client_handler.answer == answer:
                    correct_players.append(client_handler)
                else:
                    incorrect_players.append(client_handler)
            
            print(f"{c.COLOR_GREEN}Correct players: {', '.join([ch.name for ch in correct_players])}{c.COLOR_RESET}")
            print(f"{c.COLOR_RED}Incorrect players: {', '.join([ch.name for ch in incorrect_players])}{c.COLOR_RESET}")
            
            if len(correct_players) == 0:
                msg = f"{c.COLOR_RED}No one got the answer right. Trying again with a new question.{c.COLOR_RESET}"
                print(msg)
                # let players know who is still in the game:
                for ch in get_in_game_players():
                    ch.send_message(c.GENERAL_MESSAGE, msg)
            else:
                for client_handler in correct_players:
                    client_handler.correct = True

                for client_handler in incorrect_players:
                    client_handler.correct = False
                    client_handler.disqualify()
            
                # let players know who is still in the game:
                for ch in get_in_game_players():
                    msg = f"{c.COLOR_GREEN}You are correct!{c.COLOR_RESET}"
                    ch.send_message(c.GENERAL_MESSAGE, msg)
                
        
        if len(get_in_game_players()) == 1:
            GAME_RUNNING = False
            
        SENT_QUESTION = False
        ANSWERS_CHECKED = True

        with ANSWERS_CHECKED_CONDITION:
            ANSWERS_CHECKED_CONDITION.notify_all()

        round_num += 1

    winner = get_in_game_players()[0]
    print("waiting for clients to exit normally...")
    for ch in CLIENTS_HANDLERS:
        ch.join()

    return winner
    

def send_game_over_message(winner: str):
    clients_handlers = list(CLIENTS_HANDLERS)
    for ch in clients_handlers:
        msg = None
        if ch.in_game:
            msg = f"{c.COLOR_GREEN}You are the winner!{c.COLOR_RESET}"
            # add the winner to the stats
            server_stats.add_player_win(winner)
        else:
            msg = f"The winner is: {winner}"
        ch.send_message(c.GAME_OVER_MESSAGE, msg)
        ch.disconnect()

def is_game_decided(rounds_results: list[ClientHandler]) -> bool:
    counts = Counter(rounds_results)
    max_freq = max(counts.values())
    return list(counts.values()).count(max_freq) == 1


def listen(server_port: int = 0) -> None:
    global SEND_BROADCAST
    global CLIENTS_HANDLERS

    ip_address = get_ip_address()

    # Create a TCP socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        # Bind the socket to the address and port
        server_socket.settimeout(c.CLIENT_NO_JOIN_TIMEOUT_SEC)
        server_socket.bind((ip_address, server_port))
        server_port = server_socket.getsockname()[1]
        server_socket.listen()

        
        while True:
            CLIENTS_HANDLERS = []
            # broadcast invitation
            broadcast_thread = threading.Thread(target=broadcast_loop,
                                                args=(ip_address, c.SERVER_NAME, server_port))
            SEND_BROADCAST = True
            broadcast_thread.start()

            # Start listening for incoming connections
            print(f"Server started, listening on IP address {ip_address}")
            handle_incoming_connections(server_socket=server_socket)
            SEND_BROADCAST = False
            broadcast_thread.join()

            send_welcome_message()
            winner = game_loop()
            send_game_over_message(winner=winner.name)
            server_stats.print_player_wins()
        

if __name__ == '__main__':
    # listen on a random port
    listen(server_port=0)
