import socket
import threading
import struct
import time
import random

from questions import QUESTIONS
import constants as c


GAME_STARTED_CONDITION: threading.Condition = threading.Condition()
GAME_STARTED: bool = False
WAIT_FOR_ANSWERS_CONDITION: threading.Condition = threading.Condition()
ANSWERS_CHECKED_CONDITION: threading.Condition = threading.Condition()
ANSWERS_CHECKED: bool = False


class ClientHandler:
    def __init__(self, client_socket: socket.socket):
        self.thread: threading.Thread = threading.Thread(target=self.handle)
        self.socket: socket.socket = client_socket

        self.name: str = None
        self.answer: bool = None
        self.correct: bool = None
        self.in_game: bool = True

    def start(self):
        self.thread.start()

    def exit_game(self):
        self.in_game = False

    def handle(self):
        # get client name
        message = self.socket.recv(c.CLIENT_NAME_PACKET_SIZE).decode()
        self.name = message.split(c.CLIENT_NAME_TERMINATION)[0]

        # wait for game to start
        with GAME_STARTED_CONDITION:
            while not GAME_STARTED:
                GAME_STARTED_CONDITION.wait()

            self.in_game = True

        while GAME_STARTED:
            # get answer from client
            answer = None
            while answer not in c.TRUE_ANSWERS + c.FALSE_ANSWERS:
                response = self.socket.recv(c.CLIENT_ANSWER_PACKET_SIZE)
                if response == 0:
                    # client disconnected
                    print(f"{self.name} disconnected.")
                    self.exit_game()
                    return
                answer = response.decode()
                if answer not in c.TRUE_ANSWERS + c.FALSE_ANSWERS:
                    error_message = c.ERROR_MESSAGE
                    error_message += f"Invalid answer: {answer}"
                    self.socket.sendall(error_message.encode())

            with WAIT_FOR_ANSWERS_CONDITION:
                self.answer = True if answer in c.TRUE_ANSWERS else False
                WAIT_FOR_ANSWERS_CONDITION.notify()

            # wait for all answers to be checked
            with ANSWERS_CHECKED_CONDITION:
                while not ANSWERS_CHECKED:
                    ANSWERS_CHECKED_CONDITION.wait()

                if not self.correct:
                    break

            # reset answer and correct fields
            self.answer = None
            self.correct = None


SEND_BROADCAST: bool = False
CLIENTS_HANDLERS: list[ClientHandler] = []


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
        sock.bind((ip_address, c.BROADCAST_PORT))
        while SEND_BROADCAST:
            sock.sendto(udp_packet, broadcast_address)
            time.sleep(c.SERVER_BROADCAST_PERIOD_SEC)


def handle_new_connection(client_socket: socket.socket, client_address: tuple) -> None:
    print("New connection from ", client_address)
    handler: ClientHandler = ClientHandler(client_socket=client_socket)
    CLIENTS_HANDLERS.append(handler)
    handler.start()


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
    global SEND_BROADCAST

    SEND_BROADCAST = False

    welcome_message = c.WELCOME_MESSAGE
    welcome_message += f'Welcome to {c.SERVER_NAME} trivia king!\n'
    for i, client_handler in enumerate(CLIENTS_HANDLERS):
        player_name = client_handler.name
        welcome_message += f'Player {i + 1}: {player_name}\n'
    welcome_message += '==\n'

    # send welcome message to every player
    for client_handler in CLIENTS_HANDLERS:
        client_handler.socket.sendall(welcome_message.encode())

    time.sleep(c.SERVER_POST_WELCOME_PAUSE_SEC)


def game_loop():
    global GAME_STARTED

    # start the game
    GAME_STARTED = True
    with GAME_STARTED_CONDITION:
        GAME_STARTED_CONDITION.notify_all()

    in_game_players = [ch for ch in CLIENTS_HANDLERS if ch.in_game]
    selected_questions_indices = [-1]
    while len(in_game_players) > 1:
        # choose a random question
        question_index = -1
        while question_index in selected_questions_indices:
            question_index = random.randint(0, len(QUESTIONS) - 1)
        selected_questions_indices.append(question_index)
        question, answer = QUESTIONS[question_index]

        # send the question to all players
        for client_handler in in_game_players:
            client_handler.socket.sendall(
                (c.QUESTION_MESSAGE + question).encode())

        print(f"Sent question: {question}. The answer is: {answer}")

        # wait for answers
        with WAIT_FOR_ANSWERS_CONDITION:
            pending_clients = len(in_game_players)
            while pending_clients > 0:
                WAIT_FOR_ANSWERS_CONDITION.wait()
                pending_clients = len(
                    [ch for ch in in_game_players if ch.answer is None])

        # check answers
        with ANSWERS_CHECKED_CONDITION:
            for client_handler in in_game_players:
                client_handler.correct = client_handler.answer == answer
                if not client_handler.correct:
                    print(f"{client_handler.name} got the answer wrong.")
                    client_handler.exit_game()
            ANSWERS_CHECKED_CONDITION.notify_all()

        # filter players
        in_game_players = [ch for ch in CLIENTS_HANDLERS if ch.in_game]

    if len(in_game_players) == 0:
        send_game_over_message(winner=None)
    else:
        winner_client_handler = in_game_players[0]
        send_game_over_message(winner=winner_client_handler.name)


def send_game_over_message(winner: str):
    if winner is None:
        # send all client message with the winner
        for ch in CLIENTS_HANDLERS:
            ch.socket.sendall((c.GAME_OVER_MESSAGE + "No winner").encode())
        print("Game Over! (no winner)")
    else:
        # send all client message with the winner
        for ch in CLIENTS_HANDLERS:
            msg = None
            if ch.in_game:
                msg = c.GAME_OVER_MESSAGE + "You are the winner!"
            else:
                msg = c.GAME_OVER_MESSAGE + f"The winner is: {winner}"

            ch.socket.sendall(msg.encode())

        print(f"Game Over! The winner is: {winner}")


def listen(server_port: int = 0) -> None:
    global SEND_BROADCAST

    ip_address = get_ip_address()

    # Create a TCP socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        # Bind the socket to the address and port
        server_socket.settimeout(c.CLIENT_NO_JOIN_TIMEOUT_SEC)
        server_socket.bind((ip_address, server_port))
        server_port = server_socket.getsockname()[1]
        server_socket.listen()

        broadcast_thread = threading.Thread(target=broadcast_loop,
                                            args=(ip_address, c.SERVER_NAME, server_port))
        SEND_BROADCAST = True
        broadcast_thread.start()

        # Start listening for incoming connections
        # TODO: check that after the game is over, the server will run broadcast
        print(f"Server started, listening on IP address {ip_address}")
        handle_incoming_connections(server_socket=server_socket)
        send_welcome_message()
        game_loop()


if __name__ == '__main__':
    # listen on a random port
    listen(server_port=0)
