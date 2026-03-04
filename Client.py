from socket import *
import Protocol # Custom made, see Protocol.py
from dataclasses import dataclass

# Logs the given user to their account.
def log_in(clientSocket: socket) -> None:
    username = input("Please enter your username:\t")
    password  = input ("Please enter your password:\t")

    send_message(clientSocket, f"{Protocol.initiate_protocol(1)}\n{username}\n{password}\n\n")

    output = receive_message(clientSocket).strip()

    match output:
        case "OK|LOGIN_SUCCESS":
            print("Login successful!")
            load_account_menu(clientSocket, username)
        case "ERROR|LOGIN_FAILED":
            print("Login failed. Mismatching username and password.")
        case "ERROR|INVALID_LOGIN_FORMAT":
            print("Invalid login format.")
        case "ERROR|DB_ERROR":
            print("An error with the database has occured.")
        case _:
            print("Unexpected server message:\t", output)


# Made independently from the log_in function just for sanity's sake.
def create_account(clientSocket: socket) -> None:
    username = input("Enter your username:\t")
    password = input("Enter your password:\t")

    send_message(clientSocket, f"{Protocol.initiate_protocol(2)}\n{username}\n{password}\n\n")
    
    output = receive_message(clientSocket).strip() # Either can't create account due to not being able to access DB, account already exists, etc, OR account is created, with notification.

    match output:
        case "OK|SIGNUP_SUCCESSFUL":
            print("You have successfully created your account! You are currently logged in.")
            load_account_menu(clientSocket, username)
        case "ERROR|USER_ALREADY_EXISTS":
            print("Someone else is using this username.")
        case "ERROR|INVALID_CREDENTIALS":
            print("")
        case "ERROR|INVALID_CREATE_FORMAT":
            print(f"Something is wrong with the CREATE request:\t{output}")
        case _:
            print("Unexpected server message:\t", output)
    pass

# Loads the data of a newly logged in user to the terminal. This data includes:
# 1.) The user's 'contacts'. This leads to the list of contacts that the user has communicated with in the past. Text and media can be exchanged here (Media only if the other user is online (because of UDP)).
# 2.) A search menu. This allows the user to look for other users to send messages to. No need for authorisation for users to communicate for now (you can just send messages to whoever at whatever time).
# 3.) Form a group. This allows the user to form a group, of up to 5 people. TODO: Check Assignment doc for specified amount.
# 4.) A log out button. Mostly client side, will give the user the option to either state '[Y/n]'.
def load_account_menu(clientSocket: socket, username: str) -> None:
    # TODO: A method that loads up the user's contacts and text messages exchanged over here.
    print(f"Welcome {username}!\n" \
    "1. Check contacts\n" \
    "2. Search an account\n" \
    "3. Form a group\n" \
    "4. Log out\n")
    try:
        while True:
            choice = int(input())
            match choice:
                case 1:
                    handle_user_contacts(clientSocket, username)
                case 2:
                    handle_search()
                case 3:
                    handle_group_making()
                case 4:
                        if log_in(clientSocket):
                            break # Breaks out of the main while loop in order to get to the Login screen again.
                case _:
                    print("Please choose between 1 and 4.")

                
    except ValueError:
        print("Wrong number entered. Try again.")

def handle_user_contacts(clientSocket, username) -> None:
    send_message(clientSocket, f"{Protocol.initiate_protocol(6)}\n\n")

    packet = receive_packet(clientSocket)
    if not packet:
        print("No response from server.")
        return

    header = packet[0].strip()
    if header != "OK|CONTACTS":
        print("Unexpected server message:\t", header)
        return

    contacts = [line.strip() for line in packet[1:] if line.strip()]
    if not contacts:
        print("You have no contacts yet.")
        return

    print("Your contacts:")
    for c in contacts:
        print(c)

def log_out(clientSocket: socket, username: str) -> bool:
    while True:
        confirmation = str(input("Are you sure? [Y/n]\n")) 
        if confirmation.lower() in ['y', 'n']:
            break

    if confirmation.lower() == 'y':
        send_message(clientSocket, f"{Protocol.initiate_protocol(3)}\n\n") # Log out protocol
        output = receive_message(clientSocket).strip()
        if output == "OK|BYE":
            print("Logged out successfully!")
            return True
    return False


def handle_search() -> None:
    while True:
        search = input("Search for a user (Enter 'Q' or 'Quit' to stop):\t")

        # TODO: Send a 'SEARCH' protocol to the server. It verifies if the user exists. Sends a SEARCH_FAIL or SEARCH_SUCCESS.
        # If fail, then tell the user to enter a valid username (Client). Else, confirm with the user that they are currently
        # In a chatroom with the person.
        if search.lower() in ['quit', 'q']:
            break
        
    pass

def handle_group_making() -> None:
    while True:
        members = set()
        member = input("Enter a username (Enter 'Q' or 'Quit' to stop):\t")
        if member.lower() in ['quit', 'q']:
            break
        members.add(member)
    
    # TODO: Iterate through each member of the group and add them to it. Update the DB (Serverside)

    pass
    
# Will be defined in much more detail later.
def close_program(clientSocket: socket) -> None:
    send_message(clientSocket, f"{Protocol.initiate_protocol(3)}\n\n")

    output = receive_message(clientSocket).strip()
    if output == "OK|BYE":
        print("You have successfully closed the program.")
        clientSocket.close()
        quit()
    else: 
        print("Strange output message from the server received:\t", output)
    pass

def main():
    try:
        serverName = 'localhost'
        serverPort = 12000
        clientSocket = socket(AF_INET, SOCK_STREAM)
        clientSocket.connect((serverName, serverPort))
        while True:
            print("Welcome to our chat app! Press:\n" \
            "1. Log-in\n" \
            "2. Create Account\n" \
            "3. Close Program")
            num = eval(input())
            if num == 1:
                log_in(clientSocket)
            elif num == 2:
                create_account(clientSocket)
            elif num == 3:
                close_program(clientSocket)
            else:
                continue
    except ConnectionRefusedError:
        print("The connection was refused.\n" \
            "The server may be offline.")

# Sends a message to the server for simplicity. Good for small messages
def send_message(clientSocket: socket, message: str) -> None:
    clientSocket.sendall(message.encode())
    pass

# Receives a message from the server.
def receive_message(clientSocket: socket) -> str:
    return clientSocket.recv(1024).decode()

def receive_packet(clientSocket: socket) -> list:
    data = ""
    while True:
        chunk = clientSocket.recv(1024).decode(errors="ignore")
        if not chunk:
            return []
        data += chunk
        if "\n\n" in data:
            break
    packet = data.split("\n\n")[0]
    return packet.split("\n")
    

if __name__ == "__main__":
    main()