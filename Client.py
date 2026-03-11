# The client program, which must be run after the server. 
# Using ngrok means we need to change both the Server Port and Server Name during each test.

# These modules in particular are used to modify the output in the terminal.
import sys
from termcolor import colored, cprint
import tty
import termios

from socket import *
import Protocol # Custom made, see Protocol.py
from dataclasses import dataclass
import threading
import time
import ClientStates

PING_TIME = 5
SERVER_NAME = '6.tcp.ngrok.io'
TCP_SERVER_PORT = 18685
UDP_SERVER_PORT = 14400

currentState = ClientStates.State.MAIN_MENU

# Method that transitions between states in the terminal menu.
def state_control(clientSocket: socket) -> ClientStates.State:
    
    while currentState != ClientStates.State.CLOSE:
        cprint(f"{currentState}", "cyan")
        match currentState:
            case ClientStates.State.MAIN_MENU:
                load_main_menu(clientSocket)
            case ClientStates.State.ACCOUNT_MENU:
                load_account_menu(clientSocket, username)
            case ClientStates.State.CREATE_ACCOUNT:
                create_account(clientSocket)
            case ClientStates.State.LOGIN:
                log_in(clientSocket)
            case ClientStates.State.SEARCH:
                handle_search(clientSocket, username)
            case ClientStates.State.CHAT:
                start_private_chat(clientSocket, username, peer_username)
            case ClientStates.State.CONTACTS:
                handle_user_contacts(clientSocket, username)
            case ClientStates.State.GROUP:
                print("Waiting for Chandik's implementation.")
                close_program(clientSocket)
    close_program(clientSocket)
    pass

def load_main_menu(clientSocket: socket) -> None:
    global currentState
    global username
    username = None # This is to remove any po
    try:
        num = int(input("Welcome to our chat app! Press:\n" \
                        "1. Log-in\n" \
                        "2. Create Account\n" \
                        "3. Close Program\n" \
                        "> "))  

        match num:
            case 1:
                currentState = ClientStates.State.LOGIN 
            case 2:
                currentState = ClientStates.State.CREATE_ACCOUNT
            case 3:
                currentState = ClientStates.State.CLOSE

    except KeyboardInterrupt:
        currentState = ClientStates.State.CLOSE
    except ValueError:
        cprint("Please enter a number between 1 and 3.", "red")


# Logs the given user to their account.
def log_in(clientSocket: socket) -> None:
    global currentState
    global username

    username = input("Please enter your username:\t")
    password  = input ("Please enter your password:\t")

    send_message(clientSocket, f"{Protocol.initiate_protocol(1)}\n{username}\n{password}\n\n")

    output = receive_message(clientSocket).strip()

    match output:
        case "OK|LOGIN_SUCCESS":
            cprint("Login successful!", "green")
            # The UDP thread is created. This will send frequent pings to the server to communicate the user isn't sleeping.
            event = threading.Event()
            udpThread = threading.Thread(target = send_ping, args = (username, event), daemon = True)
            udpThread.start()
            currentState = ClientStates.State.ACCOUNT_MENU

        case "ERROR|LOGIN_FAILED":
            cprint("Login failed. Mismatching username and password.")
        case "ERROR|INVALID_LOGIN_FORMAT":
            cprint("Invalid login format.")
        case "ERROR|DB_ERROR":
            cprint("An error with the database has occured.")
        case _:
            cprint(f"Unexpected server message:\t{output}", "red")


# Made independently from the log_in function just for sanity's sake.
def create_account(clientSocket: socket) -> None:
    global currentState
    global username

    username = input("Enter your username:\t")
    password = input("Enter your password:\t")

    send_message(clientSocket, f"{Protocol.initiate_protocol(2)}\n{username}\n{password}\n\n")
    
    output = receive_message(clientSocket).strip() # Either can't create account due to not being able to access DB, account already exists, etc, OR account is created, with notification.

    match output:
        case "OK|SIGNUP_SUCCESSFUL":
            cprint("You have successfully created your account! You are currently logged in.", "green")
            currentState = ClientStates.State.ACCOUNT_MENU
        case "ERROR|USER_ALREADY_EXISTS":
            cprint("Someone else is using this username.", "red")
        case "ERROR|INVALID_CREDENTIALS":
            print("")
        case "ERROR|INVALID_CREATE_FORMAT":
            cprint(f"Something is wrong with the CREATE request:\t{output}", "red")
        case _:
            cprint(f"Unexpected server message:\t{output}", "red")
    pass

# Loads the data of a newly logged in user to the terminal. This data includes:
# 1.) The user's 'contacts'. This leads to the list of contacts that the user has communicated with in the past. Text and media can be exchanged here (Media only if the other user is online (because of UDP)).
# 2.) A search menu. This allows the user to look for other users to send messages to. No need for authorisation for users to communicate for now (you can just send messages to whoever at whatever time).
# 3.) Form a group. This allows the user to form a group, of up to 5 people. TODO: Check Assignment doc for specified amount.
# 4.) A log out button. Mostly client side, will give the user the option to either currentState'[Y/n]'.
def load_account_menu(clientSocket: socket, username: str) -> None:
    global currentState

    try:
        choice = int(input(f"Welcome {username}!\n" \
        "1. Check contacts\n" \
        "2. Search an account\n" \
        "3. Form a group\n" \
        "4. Log out\n" \
        "> "))
        match choice:
            case 1:
                currentState = ClientStates.State.CONTACTS
            case 2:
                currentState = ClientStates.State.SEARCH
            case 3:
                currentState = ClientStates.State.GROUP
            case 4:
                logout = str(input("You will be logged out (Type '/exit' to confirm.) >\t"))
                if logout == "/exit":
                    currentState = ClientStates.State.MAIN_MENU
                else:
                    print("You are still logged-in.")
            case _:
                cprint("Please enter a number between 1 and 4.", "red")
                
    except ValueError:
        print("Please enter a number.")
    except KeyboardInterrupt:
        currentState = ClientStates.State.CLOSE

def handle_user_contacts(clientSocket, username) -> None:
    global peer_username
    global currentState

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
    for i, c in enumerate(contacts, start=1):
        print(f"{i}) {c}")

    selection = input("Select a contact number to chat, or press Enter to go back: ").strip()
    if not selection:
        return

    try:
        idx = int(selection) 
    except ValueError:
        print("Invalid selection.")
        return

    if idx < 1 or idx > len(contacts):
        print("Invalid selection.")
        return

    peer_username = contacts[idx - 1]
    currentState = ClientStates.State.CHAT

# def start_private_chat(clientSocket: socket, my_username, peer_username):
#     send_message(clientSocket, f"{Protocol.initiate_protocol(8)}\n{peer_username}\n\n")
#     packet = receive_packet(clientSocket)
#     if not packet:
#         print("No response from server.")
#         return

#     header = packet[0].strip()
#     if header == "ERROR|NO_SUCH_USER":
#         print("No such user.")
#         return
#     if header == "ERROR|DB_ERROR":
#         print("Database error.")
#         return
#     if header != "OK|CHAT_HISTORY":
#         print("Unexpected server message:\t", header)
#         return

#     print(f"--- Chat with {peer_username} (type /exit to leave) ---")
#     for line in packet[1:]:
#         line = line.strip()
#         if not line:
#             continue
#         parts = line.split("|", 2)
#         if len(parts) == 3:
#             sender, msg, ts = parts
#             print(f"[{ts}] {sender}: {msg}")

#     stop_event = threading.Event()

#     def receiver_loop():
#         while not stop_event.is_set():
#             incoming = receive_packet(clientSocket)
#             if not incoming:
#                 break
#             kind = incoming[0].strip()
#             if kind == "INCOMING_PRIVATE" and len(incoming) >= 3:
#                 sender = incoming[1].strip()
#                 msg = incoming[2].strip()
#                 if sender == peer_username:
#                     print(f"{peer_username}: {msg}")
            
#     t = threading.Thread(target=receiver_loop, daemon=True)
#     t.start()

#     try:
#         while True:
#             msg = input("you> ")
#             if msg.strip() == "/exit":
#                 break
#             if not msg.strip():
#                 continue
#             send_message(clientSocket, f"{Protocol.initiate_protocol(4)}\n{peer_username}\n{msg}\n\n")
#     finally:
#         stop_event.set()
#         send_message(clientSocket, f"{Protocol.initiate_protocol(9)}\n{peer_username}\n\n")

def start_private_chat(clientSocket: socket, my_username: str, peer_username: str):
    send_message(clientSocket, f"{Protocol.initiate_protocol(8)}\n{peer_username}\n\n")
    packet = receive_packet(clientSocket)
    if not packet:
        print("No response from server.")
        return

    header = packet[0].strip()
    if header == "ERROR|NO_SUCH_USER":
        print("No such user.")
        return
    if header == "ERROR|DB_ERROR":
        print("Database error.")
        return
    if header != "OK|CHAT_HISTORY":
        print("Unexpected server message:\t", header)
        return

    print(f"\n--- Chat with {peer_username} (type /exit to leave) ---")
    for line in packet[1:]:
        line = line.strip()
        if not line:
            continue
        parts = line.split("|", 2)
        if len(parts) == 3:
            sender, msg, ts = parts
            print(f"[{ts}] {sender}: {msg}")

    stop_event = threading.Event()
    input_buffer = []
    buffer_lock = threading.Lock()

    def reprint_prompt():
        """Reprint the current input line cleanly."""
        with buffer_lock:
            current = "".join(input_buffer)
        sys.stdout.write(f"\ryou> {current}")
        sys.stdout.flush()

    def receiver_loop():
        while not stop_event.is_set():
            try:
                incoming = receive_packet(clientSocket)
            except Exception:
                break
            if not incoming:
                break
            kind = incoming[0].strip()

            if kind in ("OK|MESSAGE_SENT", "OK|PRIVATE_STORED", "OK|CHAT_CLOSED"):
                continue

            if kind == "INCOMING_PRIVATE" and len(incoming) >= 3:
                sender = incoming[1].strip()
                msg = incoming[2].strip()
                # Clear current line, print the message above, reprint prompt + buffer
                sys.stdout.write("\r\033[K")   # move to line start, clear it
                print(f"{sender}: {msg}")
                reprint_prompt()

    t = threading.Thread(target=receiver_loop, daemon=True)
    t.start()

    # Save terminal settings and switch to raw mode so we can read char by char
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    try:
        tty.setraw(fd)
        sys.stdout.write("\ryou> ")
        sys.stdout.flush()

        while True:
            ch = sys.stdin.read(1)

            if ch in ("\r", "\n"):  # Enter
                with buffer_lock:
                    msg = "".join(input_buffer)
                    input_buffer.clear()
                sys.stdout.write("\r\033[K")  # clear the input line
                if msg.strip() == "/exit":
                    break
                if msg.strip():
                    print(f"you>: {msg}")  # echo sent message as a chat line
                    send_message(clientSocket, f"{Protocol.initiate_protocol(4)}\n{peer_username}\n{msg}\n\n")
                sys.stdout.write("\ryou> ")
                sys.stdout.flush()

            elif ch in ("\x7f", "\x08"):  # Backspace
                with buffer_lock:
                    if input_buffer:
                        input_buffer.pop()
                sys.stdout.write("\b \b")
                sys.stdout.flush()

            elif ch == "\x03":  # Ctrl+C
                break

            else:
                with buffer_lock:
                    input_buffer.append(ch)
                sys.stdout.write(ch)
                sys.stdout.flush()

    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        stop_event.set()
        send_message(clientSocket, f"{Protocol.initiate_protocol(9)}\n{peer_username}\n\n")
        t.join(timeout=1.0)


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


def handle_search(clientSocket: socket, username: str) -> None:
    global currentState
    global peer_username
    search = input("Search for a user (Enter '/exit' to stop):\t")

    if search == "/exit":
        print()
        currentState = ClientStates.State.ACCOUNT_MENU

    send_message(clientSocket, f"{Protocol.initiate_protocol(5)}\n{search}\n\n")
    packet = receive_packet(clientSocket)
    if not packet:
        print("No response from server.")

    header = packet[0].strip()
    if header != "OK|SEARCH":
        print("Unexpected server message:\t", header)

    results = [line.strip() for line in packet[1:] if line.strip()]
    if not results:
        print("No matches.")
        

    print("Matches:")
    for i, u in enumerate(results, start=1):
        print(f"{i}) {u}")

    selection = input("Select a user number to chat, or press Enter to search again: ").strip()

    try:
        idx = int(selection)
    except ValueError:
        print("Invalid selection.")
        return
    
    if idx < 1 or idx > len(results):
        print("Invalid selection.")
    

    peer_username = results[idx - 1]
    currentState = ClientStates.State.CHAT
        
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
        cprint("You have successfully closed the program.", "green")
        clientSocket.close()
        quit()

    pass

def main():
    try:
        serverName = SERVER_NAME
        serverPort = TCP_SERVER_PORT
        clientSocket = socket(AF_INET, SOCK_STREAM)
        clientSocket.connect((serverName, serverPort))
        
        state_control(clientSocket)

    except ConnectionRefusedError as e:
        print("The connection was refused.\n" \
            "The server may be offline.\n" \
            f"{e}")

# Sends a message to the server for simplicity. Good for small messages
def send_message(clientSocket: socket, message: str) -> None:
    clientSocket.sendall(message.encode())
    pass

# UDP equivalent of the send_message method. 
def send_message_udp(message: str, udpSocket: socket, ip: str, port: int) -> None:
    udpSocket.sendto(message.encode(), (ip, port))
    pass

# Receives a message from the server.
def receive_message(clientSocket: socket) -> str:
    return clientSocket.recv(1024).decode()

# Much more elaborate variation of the receive_packet method,
# which receives the entire message in chunks rather than preemptively truncating it.
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

# Client side implementation of the ping system for UDP.
def send_ping(username: str, event: threading.Event) -> None:
    clientSocket = socket(AF_INET, SOCK_DGRAM)
    try:
        while not event.is_set():
            try:
                message = f"{Protocol.initiate_protocol(7)}|{username}"
                send_message_udp(message, clientSocket, SERVER_NAME, UDP_SERVER_PORT)
            except:
                print("An error has occured while sending a ping to the server.")

            time.sleep(PING_TIME)

        clientSocket.close()    
    except Exception as e:
        print("Send ping function experienced an error:\t", e)
    finally:
        clientSocket.close()

if __name__ == "__main__":
    main()
