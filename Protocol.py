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

# Returns string representation of a given protocol.
# TODO: Change name.
def initiate_protocol (num: int) -> str:
    return Protocol(num).name

#print(initiate_protocol(2))