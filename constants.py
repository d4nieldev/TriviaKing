LOCALHOST_ADDRESS = '127.0.0.1'
MIN_PORT = 1024
MAX_PORT = 65535
CLIENT_NAME_PACKET_SIZE = 1024
CLIENT_ANSWER_PACKET_SIZE = 1

BROADCAST_ADDRESS = '<broadcast>'
BROADCAST_PORT = 13117
BROADCAST_MAGIC_COOKIE = 0xabcddcba
BROADCAST_MESSAGE_TYPE = 0x2

CLIENT_NAME_TERMINATION = '\n'
SERVER_MSG_TERMINATION = '\0'
CLIENT_NO_JOIN_TIMEOUT_SEC = 10

CLIENT_STATE_LOOKING_FOR_SERVER = 'looking_for_server'
CLIENT_STATE_CONNECTING_TO_SERVER = 'connecting_to_server'
CLIENT_STATE_GAME_MODE = 'game_mode'
MIN_NUM_BOTS = 1
MAX_NUM_BOTS = 7
CLIENT_TEAM_NAMES = [
    "Hateful Brains",
    "Bill's Quizmasters",
    "Trivia Reservoirs",
    "Inglourious Know-it-Alls",
    "Cheesy Royale Quizzers",
    "Cult Fiction Fact-Checkers",
    "Bloody Brilliant Minds",
    "Fellowship of the Quiz",
    "The Godfather’s Godchildren",
    "Shutter Island Shapeshifters",
    "Sherlocked Minds",
    "Quizteros of Westeros",
    "The Big Bang Queries",
    "Stranger Thinkers",
    "Breaking Bads",
    "Peaky Minders"
]

SERVER_NAME = 'NovaBeach'
SERVER_NO_ANSWER_TIMEOUT_SEC = 10
SERVER_BROADCAST_PERIOD_SEC = 1
SERVER_POST_WELCOME_PAUSE_SEC = 2
TRUE_ANSWERS = ['Y', 'T', '1']
FALSE_ANSWERS = ['N', 'F', '0']
MIN_ROUNDS = 3

# message types
WELCOME_MESSAGE = '[W]'
ERROR_MESSAGE = '[E]'
QUESTION_MESSAGE = '[Q]'
GENERAL_MESSAGE = '[G]'
GAME_OVER_MESSAGE = '[GO]'

# color asci
COLOR_RESET = "\033[0m"
COLOR_RED = "\033[91m"
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_BLUE = "\033[94m"
COLOR_MAGENTA = "\033[95m"
COLOR_CYAN = "\033[96m"

# STATS 
FILE_PATH_WINS = 'player_wins.txt'
