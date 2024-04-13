import constants as c
import sys


def handle():
    # common logic
    # wait for broadcast
    # change state
    # open TCP
    # receive question
    pass


def handle_bot():
    # send answer bot
    handle()


def handle_human():
    # send answer human
    handle()


if __name__ == "__main__":
    if len(sys.argv) == 2:
        if sys.argv[1] == 'bot':
            # be bot
            handle_bot()
    # be human
    handle_human()
