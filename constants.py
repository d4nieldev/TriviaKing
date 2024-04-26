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
SERVER_POST_GAME_OVER_DISCONNECT_TIMEOUT_SEC = 3
MIN_TEAMS = 2

CLIENT_STATE_LOOKING_FOR_SERVER = 'looking_for_server'
CLIENT_STATE_CONNECTING_TO_SERVER = 'connecting_to_server'
CLIENT_STATE_GAME_MODE = 'game_mode'
CLIENT_TEAM_NAMES = [
    "Hateful Brains",
    "Bill's Quizmasters",
    "Trivia Reservoirs",
    "Inglourious Know-it-Alls",
    "Cheesy Royale Quizzers",
    "Cult Fiction Fact-Checkers",
    "Bloody Brilliant Minds",
    "Fellowship of the Quiz",
    "Shutter Island Shapeshifters",
    "Sherlocked Minds",
    "Quizteros of Westeros",
    "The Big Bang Queries",
    "Stranger Thinkers",
    "Breaking Bads",
    "Peaky Minders",
    "Quizzy Business",
    "The Quizzical Geniuses",
    "Brainy Bunch of Buffoons",
    "The Quizzy Dream Team",
    "Cerebral Assassins",
    "The Brainstorming Bandits",
    "The Quizzical Wizards",
    "The Quizzy Connoisseurs",
    "The Trivia Troopers",
    "The Quiztastic Voyage",
    "The Brainiac Bonanza",
    "The Quizzy Mavericks",
    "The Trivia Titans",
    "The Mindbenders Society",
    "The Quizzical Conundrums",
    "The Brainiac Brigade"
]
BOT_LEVELS = {'a':0.8, 'b': 0.65, 'c':0.4, 'd':0.15}

SERVER_NAME = 'NovaBeach'
SERVER_NO_ANSWER_TIMEOUT_SEC = 20
SERVER_BROADCAST_PERIOD_SEC = 1
ROUND_PAUSE_SEC = 1
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
FILE_PATH_WINS = 'NovaBeach_Champs.json'
PODIUM_STR = '''
NovaBeach Server All-Time Winners Podium:

                                {}👑
                              ______________________________
                 
{}🥈        
______________________________          
                                                                {}🥉
                                                              ______________________________
                                                                                                

May the odds be ever in your favor!



Full players rank:

{}
'''
