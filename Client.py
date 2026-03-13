from socket import *
import Protocol # Custom made, see Protocol.py
from dataclasses import dataclass
import threading
import p2p

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
    "3. Create group\n" \
    "4. My groups\n" \
    "5. Log out\n")
    try:
        while True:
            choice = int(input())
            match choice:
                case 1:
                    handle_user_contacts(clientSocket, username)
                case 2:
                    handle_search(clientSocket, username)
                case 3:
                    handle_group_making(clientSocket, username)
                case 4:
                    handle_group_list(clientSocket, username)
                case 5:
                        if log_out(clientSocket, username):
                            break # Breaks out of the main while loop in order to get to the Login screen again.
                case _:
                    print("Please choose a valid option.")

                
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
    start_private_chat(clientSocket, username, peer_username)

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

import sys
import tty
import termios

def start_private_chat(clientSocket: socket, my_username, peer_username):
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

            if kind in ("OK|MESSAGE_SENT", "OK|PRIVATE_STORED", "OK|CHAT_CLOSED",
                        "OK|BLOB_NOTIFY_SENT", "ERROR|PEER_OFFLINE", "ERROR|NOTIFY_FAILED"):
                continue

            if kind == "INCOMING_PRIVATE" and len(incoming) >= 3:
                sender = incoming[1].strip()
                msg = incoming[2].strip()
                # Clear current line, print the message above, reprint prompt + buffer
                sys.stdout.write("\r\033[K")   # move to line start, clear it
                print(f"{sender}: {msg}")
                reprint_prompt()

            elif kind == "BLOB_OFFER" and len(incoming) >= 5:
                # BLOB_OFFER\n<sender>\n<ngrok_host>\n<ngrok_port>\n<filename>
                blob_sender   = incoming[1].strip()
                blob_host     = incoming[2].strip()
                blob_port     = int(incoming[3].strip())
                blob_filename = incoming[4].strip()
                sys.stdout.write("\r\033[K")
                print(f"[File incoming from {blob_sender}: '{blob_filename}']")
                reprint_prompt()
                threading.Thread(
                    target=p2p.receive_blob,
                    args=(blob_host, blob_port, blob_filename),
                    daemon=True
                ).start()

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
                if msg.strip().startswith("/sendfile "):
                    file_path = msg.strip()[len("/sendfile "):].strip()
                    p2p.send_blob(file_path, clientSocket, my_username, peer_username)
                    sys.stdout.write("\ryou> ")
                    sys.stdout.flush()
                    continue
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
    while True:
        search = input("Search for a user (Enter 'Q' or 'Quit' to stop):\t")

        if search.lower() in ['quit', 'q']:
            break

        send_message(clientSocket, f"{Protocol.initiate_protocol(5)}\n{search}\n\n")
        packet = receive_packet(clientSocket)
        if not packet:
            print("No response from server.")
            continue

        header = packet[0].strip()
        if header != "OK|SEARCH":
            print("Unexpected server message:\t", header)
            continue

        results = [line.strip() for line in packet[1:] if line.strip()]
        if not results:
            print("No matches.")
            continue

        print("Matches:")
        for i, u in enumerate(results, start=1):
            print(f"{i}) {u}")

        selection = input("Select a user number to chat, or press Enter to search again: ").strip()
        if not selection:
            continue
        try:
            idx = int(selection)
        except ValueError:
            print("Invalid selection.")
            continue
        if idx < 1 or idx > len(results):
            print("Invalid selection.")
            continue

        peer_username = results[idx - 1]
        start_private_chat(clientSocket, username, peer_username)
        
    pass

def handle_group_making(clientSocket: socket, username: str) -> None:
    group_name = input("Enter group name: ").strip()
    if not group_name:
        print("Group name cannot be empty.")
        return

    members = []
    print("Enter usernames to add. Type Q to stop.")
    while True:
        member = input("Add member: ").strip()
        if member.lower() in ['quit', 'q']:
            break
        if not member:
            continue
        if member == username:
            print("You are already added automatically.")
            continue
        if member not in members:
            members.append(member)
    
    lines = [Protocol.initiate_protocol(12), group_name] + members
    send_message(clientSocket, "\n".join(lines) + "\n\n")

    packet = receive_packet(clientSocket)
    if not packet:
        print("No response from server.")
        return
    
    header = packet[0].strip()
    if header.startswith("OK|GROUP_CREATED|"):
        group_id = header.split("|")[2]
        print(f"Group created successfully. Group ID: {group_id}")
    elif header == "ERROR|INVALID_GROUP_NAME":
        print("Invalid group name.")
    elif header == "ERROR|DB_ERROR":
        print("Database error.")
    else:
        print("Unexpected server message:", header)
    
    # TODO: Iterate through each member of the group and add them to it. Update the DB (Serverside)

def handle_group_list(clientSocket: socket, username: str) -> None:
    send_message(clientSocket, f"{Protocol.initiate_protocol(13)}\n\n")

    packet = receive_packet(clientSocket)
    if not packet:
        print("No response from server.")
        return
    
    header = packet[0].strip()
    if header != "OK|GROUPS":
        print("Unexpected server message:", header)
        return
    
    groups = []
    for line in packet[1: ]:
        line = line.strip()
        if not line:
            continue
        parts = line.split("|", 1)
        if len(parts) == 2:
            group_id, group_name = parts
            groups.append((group_id, group_name))

    if not groups:
        print("You are not in any groups yet.")
        return
    
    print("Your groups:")
    for i, (_, group_name) in enumerate(groups, start=1):
        print(f"{i}) {group_name}")
    
    selection = input("Select a group number to open, or press Enter to go back: ").strip()
    if not selection:
        return
    
    try:
        idx = int(selection)
    except ValueError:
        print("Invalid selection.")
        return

    if idx < 1 or idx > len(groups):
        print("Invalid selection.")
        return
    
    group_id, group_name = groups[idx - 1]
    start_group_chat(clientSocket, username, group_id, group_name)

def start_group_chat(clientSocket: socket, my_username: str, group_id: str, group_name: str):
    send_message(clientSocket, f"{Protocol.initiate_protocol(14)}\n{group_id}\n\n")
    packet = receive_packet(clientSocket)

    if not packet:
        print("No response from server.")
        return
    
    header = packet[0].strip()
    if header == "ERROR|NOT_IN_GROUP":
        print("You are not a member of this group.")
        return
    if header == "ERROR|DB_ERROR":
        print("Database error.")
        return
    if header != "OK|GROUP_HISTORY":
        print("Unexpected server message: ", header)
        return
    
    print(f"\n---Group chat: {group_name} (type /exit to leave) ---")
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
            if kind in ("OK|GROUP_MESSAGE_SENT", "OK|GROUP_CLOSED", "OK|MEMBER_ADDED"):
                continue
            if kind == "ERROR|ALREADY_IN_GROUP":
                sys.stdout.write("\r\033[K")
                print("[User is already in this group]")
                reprint_prompt()
                continue
            if kind == "ERROR|NO_SUCH_USER":
                sys.stdout.write("\r\033[K")
                print("[No such user]")
                reprint_prompt()
                continue
            if kind == "ERROR|NOT_IN_GROUP":
                sys.stdout.write("\r\033[K")
                print("[You are not a member of this group]")
                reprint_prompt()
                continue
            if kind == "INCOMING_GROUP" and len(incoming) >= 4:
                incoming_group_id = incoming[1].strip()
                sender = incoming[2].strip()
                msg = incoming[3].strip()

                if incoming_group_id == str(group_id):
                    sys.stdout.write("\r\033[K")
                    print(f"{sender}: {msg}")
                    reprint_prompt()

    t = threading.Thread(target=receiver_loop, daemon=True)
    t.start()

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    try:
        tty.setraw(fd)
        sys.stdout.write("\ryou> ")
        sys.stdout.flush()

        while True:
            ch = sys.stdin.read(1)

            if ch in ("\r", "\n"):
                with buffer_lock:
                    msg = "".join(input_buffer)
                    input_buffer.clear()
                sys.stdout.write("\r\033[K")

                if msg.strip() == "/exit":
                    break

                if msg.strip().startswith("/add "):
                    new_member = msg.strip()[len("/add "):].strip()
                    if new_member:
                        print(f"adding member: {new_member}")
                        send_message(clientSocket, f"{Protocol.initiate_protocol(17)}\n{group_id}\n{new_member}\n\n")
                    sys.stdout.write("\ryou> ")
                    sys.stdout.flush()
                    continue

                if msg.strip():
                    print(f"you: {msg}")
                    send_message(clientSocket, f"{Protocol.initiate_protocol(15)}\n{group_id}\n{msg}\n\n")

                sys.stdout.write("\ryou> ")
                sys.stdout.flush()

            elif ch in ("\x7f", "\x08"):
                with buffer_lock:
                    if input_buffer:
                        input_buffer.pop()
                sys.stdout.write("\b \b")
                sys.stdout.flush()

            elif ch == "\x03":
                break
            else:
                with buffer_lock:
                    input_buffer.append(ch)
                sys.stdout.write(ch)
                sys.stdout.flush()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        stop_event.set()
        send_message(clientSocket, f"{Protocol.initiate_protocol(16)}\n{group_id}\n\n")
        t.join(timeout=1.0)

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
        serverName = '0.tcp.sa.ngrok.io' # ======================================================================================================================
        serverPort = 19777
        clientSocket = socket(AF_INET, SOCK_STREAM)
        clientSocket.connect((serverName, serverPort))
        while True:
            print("Welcome to our chat app! Press:\n" \
            "1. Log-in\n" \
            "2. Create Account\n" \
            "3. Close Program")
            num = int(input())
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
