from socket import *
import Protocol # Custom made, see Protocol.py
from dataclasses import dataclass

@dataclass(frozen=True)
class Account:
    username = str
    password = str

# This method creates a temporary user whose details will be compared to the details on the server.
def create_temp_user(username: str,  password: str) -> list:
    temp = [username, password]
    return temp

# Logs the given user to their account.
def log_in(clientSocket: socket) -> None:
    username = input("Please enter your username:\t")
    password  = input ("Please enter your password:\t")
    temp = create_temp_user(username, password)
    send_message(clientSocket, f"{Protocol.initiate_protocol(1)}\n{temp[0]}\n{temp[1]}\n\n")

    text = receive_message(clientSocket)

    print(text)
    if text == "Would you like to make an account?[Y/n]:\t":
        confirmation = input()
        if confirmation.lower() == "y":
            # send confirmation to create account to server.
            pass

def create_account(clientSocket: socket) -> None:
    username = input("Enter your username:\t")
    password = input("Enter your password:\t")
    #TODO: Verify that the username does not already exist in the database.
    send_message(clientSocket, f"{Protocol.initiate_protocol(2)}\n{username}\n{password}")

    output = receive_message(clientSocket) # Either can't create account due to not being able to access DB, account already exists, etc, OR account is created, with notification.

    if output == Protocol.initiate_protocol(4): #FIXME: Assume CREATE_ACCOUNT_SUCCESS. Will be changed, just waiting for changes on the serverside and the protocol.py.
        send_message(clientSocket, f"{Protocol.initiate_protocol(2)}\n{username}\n{password}") # Send new user details to the server. Creates an account on the serverside.
        print("Account has been successfully created. You are now logged in.")
    elif output == Protocol.initiate_protocol(5): # FIXME: Assume CREATE_ACCOUNT_FAILURE.
        # TODO: Figure out if a message REALLY needs to be sent.
        print("Account has not been created due to a possible error.")
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
                    pass
                case 2:
                    pass
                case 3:
                    pass
                case 4:
                    while True:
                        confirmation = str(input("Are you sure? [Y/n]\n")) 
                        if confirmation in ['y', 'n']:
                            break

                    if confirmation.lower() == 'y':
                        send_message(clientSocket, f"{Protocol.initiate_protocol(1000000)}") # TODO: Log out protocol
                        print("Logged out successfully.") # May be an issue if not.
                        break # Breaks out of the main while loop.

                
    except ValueError:
        print("Wrong number entered. Try again.")

    
# Will be defined in much more detail later.
def close_program(clientSocket: socket):
    send_message(clientSocket, f"{Protocol.initiate_protocol(3)}\n\n")
    print("You have successfully closed the program.")
    clientSocket.close()
    quit()
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
        clientSocket.close()
    except ConnectionRefusedError:
        print("The connection was refused.\nThe server may be offline.")

# Sends a message to the server for simplicity.
def send_message(clientSocket: socket, message: str) -> None:
    clientSocket.sendall(message.encode())
    pass

# Receives a message from the server.
def receive_message(clientSocket: socket) -> str:
    return clientSocket.recv(1024).decode()
    

if __name__ == "__main__":
    main()