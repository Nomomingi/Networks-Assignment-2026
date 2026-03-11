# States for the Client.py. Makes for easier understanding of program logic.
from enum import Enum

class State (Enum):
    MAIN_MENU = 1
    LOGIN = 2
    CREATE_ACCOUNT = 3
    ACCOUNT_MENU = 4
    GROUP = 5
    SEARCH = 6
    CHAT = 7
    CONTACTS = 8
    CLOSE = 9

currentState = State.MAIN_MENU