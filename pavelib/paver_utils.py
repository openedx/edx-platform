# utility functions

PURPLE = '\033[95m'
BLUE = '\033[94m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
ENDC = '\033[0m'


def colorize_red(msg):
    return(RED + msg + ENDC)


def print_yellow(msg):
    print(YELLOW + msg + ENDC)


def print_red(msg):
    print(RED + msg + ENDC)


def print_green(msg):
    print(GREEN + msg + ENDC)


def print_blue(msg):
    print(BLUE + msg + ENDC)
