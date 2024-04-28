# Packet Sizes
CLIENT_NAME_PACKET_SIZE = 1024
CLIENT_ANSWER_PACKET_SIZE = 1

# Broadcast Packet
BROADCAST_ADDRESS = '<broadcast>'
BROADCAST_PORT = 13117
BROADCAST_MAGIC_COOKIE = 0xabcddcba
BROADCAST_MESSAGE_TYPE = 0x2

# Termination Signals
CLIENT_NAME_TERMINATION = '\n'
SERVER_MSG_TERMINATION = '\0'

# Server Consts
CLIENT_NO_JOIN_TIMEOUT_SEC = 10
SERVER_POST_GAME_OVER_DISCONNECT_TIMEOUT_SEC = 3
MIN_TEAMS = 2
SERVER_NAME = 'NovaBeach'
SERVER_NO_ANSWER_TIMEOUT_SEC = 20
SERVER_BROADCAST_PERIOD_SEC = 1
ROUND_PAUSE_SEC = 1
TRUE_ANSWERS = ['Y', 'T', '1']
FALSE_ANSWERS = ['N', 'F', '0']
MIN_ROUNDS = 3
GOOGLE_ADDRESS = ('8.8.8.8', 80)

# Message Types
WELCOME_MESSAGE = '[W]'
ERROR_MESSAGE = '[E]'
QUESTION_MESSAGE = '[Q]'
GENERAL_MESSAGE = '[G]'
GAME_OVER_MESSAGE = '[GO]'

# Client / Bot Consts
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
    "The Brainiac Brigade",
    "Puzzle Masters League",
    "Quizzards of the Coast",
    "Fact Frenzy Fighters",
    "Brainy Brawlers",
    "Pulp Quiztion",
    "Eternal Sunshine of the Spotless Minders",
    "Quizocalypse Now",
    "Quizception",
    "Pandora's Quizbox",
    "The Cinephile Cerebros",
    "Mind Palace Guards",
    "Brainy Bondsmen",
    "Witty Warriors",
    "Fact or Fiction Phalanx",
    "Scholarly Savants",
    "Westeros Wordsmiths",
    "The Periodic Quizzers",
    "Riddle Me This",
    "The Enlightened Enigmas",
    "The Quizcraft Caravan",
    "The Cognitive Crew",
    "The Trivia Trailblazers",
    "The Knowledge Knights",
    "Quizantine Empire",
    "Brain Busters Battalion",
    "The Pondering Prodigies",
    "Trivia Templars",
    "The Fact Faction",
    "Cranial Crusaders",
    "The Oracle Ops",
    "Riddler’s Retreat",
    "Jeopardy Giants",
    "Viking Vocab Vanquishers",
    "Sphinx’s Riddle Raiders",
    "Knowledge Nomads",
    "Cryptic Crusaders",
    "Quantum Questers",
    "Mythical Mavericks",
    "Echoes of Einstein",
    "Socratic Circles",
    "Factoid Pharaohs",
    "Lexicon Lions",
    "Mental Gladiators",
    "Alpha Brainiacs",
    "Omega Scholars",
    "Pinnacle Pundits",
    "Neuron Navigators",
    "Saga Scholars",
    "Chronicle Crusaders",
    "Renaissance Raiders",
    "Episteme Entities",
    "Nobel Minds",
    "Cerebral Centurions",
    "Intellect Inceptors",
    "Paragon Pathfinders",
    "Dialectic Dynamos",
    "Erudite Elites",
    "Logos Legends",
    "Aeon Academics",
    "Temporal Thinkers",
    "Virtue Voyagers",
    "Wisdom Wanderers",
    "Insight Incubators",
    "Cognition Commanders",
    "Perception Pioneers",
    "Idea Illuminators",
    "Mindful Monarchs",
    "Savvy Sages"
]
BOT_LEVELS = {'a':0.8, 'b': 0.65, 'c':0.4, 'd':0.15}
MIN_BOT_ID = 1
MAX_BOT_ID = 9999999999
BOT_NAME_FORMAT = 'BOT_#{id}'
CLIENT_INPUT_REFRESH_SEC = 0.1
PLAYER_TYPE = 'p'
BOT_TYPE = 'b'

# Colors
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
