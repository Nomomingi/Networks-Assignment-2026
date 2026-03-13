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
    SEND_BLOB= 10
    RECIEVE_BLOB = 11
    GROUP_CREATE = 12
    GROUP_LIST = 13
    GROUP_OPEN = 14
    GROUP_MESSAGE = 15
    GROUP_CLOSE = 16
    GROUP_ADD_MEMBER = 17

# Returns string representation of a given protocol.
# TODO: Change name.
def initiate_protocol (num: int) -> str:
    return Protocol(num).name

#print(initiate_protocol(2))