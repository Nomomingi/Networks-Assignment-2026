# States for the Client.py. Makes for easier understanding of program logic.

"""Client state machine definitions.

`Client.py` is written as a simple menu-driven state machine:

- The global `currentState` value decides which screen/loop runs next.
- `state_control()` dispatches to the right handler based on this enum.

This module exists so the states are defined in one place and can be referenced
cleanly throughout the client.
"""

from enum import Enum

class State (Enum):
    """All high-level screens / modes the client can be in."""
    MAIN_MENU = 1
    LOGIN = 2
    CREATE_ACCOUNT = 3
    ACCOUNT_MENU = 4
    GROUP = 5
    SEARCH = 6
    CHAT = 7
    CONTACTS = 8
    CLOSE = 9
    MAKE_GROUP = 10
    GROUP_CHATS = 11

currentState = State.MAIN_MENU