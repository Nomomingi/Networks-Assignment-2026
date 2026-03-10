# Class that makes it easier to copy over Protocol name logic,
# instead of having to retype it each time.

from enum import Enum

class Protocol(Enum):
    LOGIN = 1   # For logging into account.
    CREATE = 2  # For account creation.
    CLOSE = 3 # For closing the program.
    PRIVATE = 4 # For sending a private message to another user.
    SEARCH = 5
    CONTACTS = 6
    PING = 7 # For the UDP pinging.
    OPEN_CHAT = 8
    CLOSE_CHAT = 9
    GROUP_CREATE = 10
    GROUP_LIST = 11
    GROUP_OPEN = 12
    GROUP_MESSAGE = 13
    GROUP_CLOSE = 14

# Returns string representation of a given protocol.
# TODO: Change name.
def initiate_protocol (num: int) -> str:
    return Protocol(num).name

#print(initiate_protocol(2))