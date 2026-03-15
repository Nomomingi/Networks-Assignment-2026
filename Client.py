# The client program, which must be run after the server. 
# Using ngrok means we need to change both the Server Port and Server Name during each test.

"""Terminal client for the chat application.

This client connects to `Server.py` over TCP and speaks a simple text protocol.

Packet framing
- Messages are sent as multiple lines separated by `\n`.
- Each packet ends with a blank line (`\n\n`).
- Line 0 is always the action (e.g. `LOGIN`, `PRIVATE`, `GROUP_MESSAGE`).

Program structure
- The UI is a small *state machine*.
- The global `currentState` determines which menu or chat loop runs.
- `state_control()` repeatedly dispatches to the handler for the active state.

Realtime behavior
- During private/group chats, a background receiver thread reads packets from
  the server and prints incoming messages while you type.

File transfer
- Files are transferred peer-to-peer using `p2p.py` and ngrok.
- The server is only used for signaling (sharing the ngrok host/port).
"""

# These modules in particular are used to modify the output in the terminal.
import sys
from termcolor import colored, cprint
from rich.panel import Panel
from rich.console import Console
from rich import print
import pyfiglet

try:
    import tty
    import termios
except:
    cprint("TTY/ Termios not found. Try running the program on WSL/Linux.", "red")
    quit()    

from socket import *
import Protocol # Custom made, see Protocol.py
from dataclasses import dataclass
import threading
import p2p
import time
import ClientStates # Custom made, see ClientStates.py

PING_TIME = 5
SERVER_NAME = '145.241.187.87' # Of the Oracle Server.
TCP_SERVER_PORT = 14532
UDP_SERVER_PORT = 14400
CHARACTER_LIMIT = 250
console = Console()

currentState = ClientStates.State.MAIN_MENU

def state_control(clientSocket: socket) -> ClientStates.State:
    '''Acts as the main hub for the currentState. 
    The currentState is global and modified within the methods of this program.
    '''   
    while currentState != ClientStates.State.CLOSE:
        #cprint(f"{currentState}", "cyan")
        try:
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
                    start_group_chat(clientSocket, username, group_id, group_name)
                case ClientStates.State.MAKE_GROUP:
                    handle_group_making(clientSocket, username)
                case ClientStates.State.GROUP_CHATS:
                    handle_group_list(clientSocket, username)
        except KeyboardInterrupt:
            close_program(clientSocket)

    close_program(clientSocket)
    pass

def load_main_menu(clientSocket: socket) -> None:
    '''The main menu of the program, with the following options:'
    1.) Login, which allows the user to login to an account they own.
    2.) Create Account, which allows the user to create their account.
    3.) Close program, which kills the clientSocket.
    '''
    global currentState
    global username
    username = None
    try:
        banner = pyfiglet.figlet_format("Welcome!", width=50)
        print("[cyan]" + banner + "[/cyan]")
        console.print(
            Panel(
                "1. Log-in\n2. Create Account\n3. Close Program",
                title="[cyan bold]Main Menu[/bold cyan]", border_style="cyan",
                expand=False,
                padding=(0,1)
            )
        )

        num = int(input("> "))

        match num:
            case 1:
                currentState = ClientStates.State.LOGIN 
            case 2:
                currentState = ClientStates.State.CREATE_ACCOUNT
            case 3:
                currentState = ClientStates.State.CLOSE
            case _:
                cprint("Please enter a number between 1 and 3.", "red")

    except KeyboardInterrupt:
        currentState = ClientStates.State.CLOSE
    except ValueError:
        cprint("Please enter a number between 1 and 3.", "red")

# Logs the given user to their account.
def log_in(clientSocket: socket) -> None:
    """Prompt for username/password and send a `LOGIN` request.

    On success, starts a background UDP ping thread (`send_ping`) so the server
    can track that this user is still active.
    """
    global currentState
    global username

    username = input("Please enter your username:\t")
    password  = input ("Please enter your password:\t")

    send_message(clientSocket, f"{Protocol.initiate_protocol(1)}\n{username}\n{password}\n\n")

    output = receive_message(clientSocket).strip()

    match output:
        case "OK|LOGIN_SUCCESS":
            cprint("\nLogin successful!", "green")
            # The UDP thread is created. This will send frequent pings to the server to communicate the user isn't sleeping.
            event = threading.Event()
            udpThread = threading.Thread(target = send_ping, args = (username, event), daemon = True)
            udpThread.start()
            currentState = ClientStates.State.ACCOUNT_MENU
            return
        case "ERROR|LOGIN_FAILED":
            cprint("Login failed. Mismatching username and password.", "red")
        case "ERROR|INVALID_LOGIN_FORMAT":
            cprint("Invalid login format.", "red"),
        case "ERROR|DB_ERROR":
            cprint("An error with the database has occured.", "red")
        case _:
            cprint(f"Unexpected server message:\t{output}", "red")
    username = None


# Made independently from the log_in function just for sanity's sake.
def create_account(clientSocket: socket) -> None:
    """Prompt for username/password and send a `CREATE` request."""
    global currentState
    global username

    username = input("Enter your username:\t")
    password = input("Enter your password:\t")

    send_message(clientSocket, f"{Protocol.initiate_protocol(2)}\n{username}\n{password}\n\n")
    
    output = receive_message(clientSocket).strip() # Either can't create account due to not being able to access DB, account already exists, etc, OR account is created, with notification.

    match output:
        case "OK|SIGNUP_SUCCESSFUL":
            cprint("You have successfully created your account! You can now login to your account.", "green")
            currentState = ClientStates.State.LOGIN
            return
        case "ERROR|USER_ALREADY_EXISTS":
            cprint("Someone else is using this username.", "red")
        case "ERROR|INVALID_CREDENTIALS":
            cprint("Credentials are incorrect.", "red")
        case "ERROR|INVALID_CREATE_FORMAT":
            cprint(f"Something is wrong with the CREATE request:\t{output}", "red")
        case _:
            cprint(f"Unexpected server message:\t{output}", "red")
    username = None

def load_account_menu(clientSocket: socket, username: str) -> None:
    '''
    Loads the data of a newly logged in user to the terminal. This data includes:
    1.) The user's 'contacts'. This leads to the list of contacts that the user has communicated with in the past. Text and media can be exchanged here (Media only if the other user is online (because of UDP)).
    2.) The user's group chats. Shows a list of them (if in any).
    3.) A search menu. This allows the user to look for other users to send messages to. No need for authorisation for users to communicate for now (you can just send messages to whoever at whatever time).
    4.) Allows the client to make a Group chat.
    5.) A log out button. Mostly client side, will give the user the option to either currentState'[Y/n]'.
    '''
     
    global currentState

    try:
        text = f"Welcome, {username}"
        account_banner = pyfiglet.figlet_format(text, width=50)
        cprint(account_banner, "cyan")

        console.print(Panel("1. Check contacts\n2. Check groups\n3. Search Contact\n4. Make Group\n5. Log out",
            title="[cyan bold]Account Menu[/bold cyan]",
            border_style="cyan",
            expand=False,
            padding=(0,1) ))
        
        choice = int(input("> "))

        match choice:
            case 1:
                currentState = ClientStates.State.CONTACTS
            case 2:
                currentState = ClientStates.State.GROUP_CHATS
            case 3:
                currentState = ClientStates.State.SEARCH
            case 4:
                currentState = ClientStates.State.MAKE_GROUP
            case 5:
                console.print("[red]You will be logged out (Type [bold yellow]/exit[/bold yellow] to confirm)[/red]")
                logout = str(input("> "))
                if logout == "/exit":
                    currentState = ClientStates.State.MAIN_MENU
                else:
                    print("You are still logged-in.")
            case _:
                cprint("Please enter a number between 1 and 5.", "red")
                
    except ValueError:
        cprint("Please enter a number.", "red")
    except KeyboardInterrupt:
        currentState = ClientStates.State.CLOSE

def handle_user_contacts(clientSocket, username) -> None:
    '''Show contacts and start a private chat with the selected user.'''
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
        currentState = ClientStates.State.ACCOUNT_MENU
        return

    print("Your contacts:")
    contact_entries = []
    for i, c in enumerate(contacts, start=1):
        if c == username:
            continue
            
        if "|" in c:
            name, status = c.split("|")
            status_display = "[green]● Online[/green]" if status == "ONLINE" else "[white dim]○ Offline[/white dim]"
            contact_entries.append(f"{i}) [bold]{name:<20}[/bold] {status_display}")
        else:
            contact_entries.append(f"{i}) {c}")

    panel_content = "\n".join(contact_entries)

    console.print(Panel(panel_content, title="[bold blue]Your Contacts[/bold blue]", subtitle="[dim]Select a number to start chatting[/dim]",expand=False,border_style="cyan", padding=(1, 2)))

    selection = input("\nOR Press Enter to go back.").strip()

    if not selection:
        currentState = ClientStates.State.ACCOUNT_MENU
        return

    try:
        idx = int(selection) 
    except ValueError:
        print("Invalid selection.")
        return

    if idx < 1 or idx > len(contacts):
        print("Invalid selection.")
        return

    temp_peer_username = contacts[idx - 1]
    peer_username = temp_peer_username.split("|")[0] if "|" in temp_peer_username else temp_peer_username

    currentState = ClientStates.State.CHAT

def start_private_chat(clientSocket: socket, my_username: str, peer_username: str):
    '''
    Allows the user to engage in a private chat with another account. Commands are given as follows:
    1.) /sendfile allows the user to send a file to another user (the file's absolute path is important here).
    2.) /exit allows the user to exit the chat.
    '''
    global currentState

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

    chat_menu = (
        f"Now chatting with [green bold]{peer_username}[/green bold].\n\n"
        "1.) [purple bold]/sendfile[/purple bold] [yellow]<absolute path>[/yellow]: Send a file.\n"
        "2.) [purple bold]/exit[/purple bold]: Leave the chat."
    )

    console.print(Panel(chat_menu, title="[bold cyan]Private Chat[/bold cyan]", expand=False, border_style="bright_magenta"))

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
                    currentState = ClientStates.State.ACCOUNT_MENU
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
                    else:
                        sys.stdout.write("\a") 
                        sys.stdout.flush() 

            elif ch == "\x03":  # Ctrl+C
                break

            else:
                with buffer_lock:
                    if len(input_buffer) < CHARACTER_LIMIT:
                        input_buffer.append(ch)
                        sys.stdout.write(ch)
                        sys.stdout.flush()

    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        stop_event.set()
        send_message(clientSocket, f"{Protocol.initiate_protocol(9)}\n{peer_username}\n\n")
        t.join(timeout=1.0)


def handle_search(clientSocket: socket, username: str) -> None:
    '''Searches for the user within the database, according to specified username
    A slight tangent, but the user is able to search for themselves, and interact with themselves.
    Bug, or a stroke of genius? Who knows anymore.
    '''

    global currentState
    global peer_username

    while True:
        search = input("Search for a user (Enter '/exit' to stop):\t").strip()

        if search == "/exit":
            currentState = ClientStates.State.ACCOUNT_MENU
            return

        send_message(clientSocket, f"{Protocol.initiate_protocol(5)}\n{search}\n\n")
        response = receive_packet(clientSocket)
        
        if not response:
            print("No response from server.")
            return

        header = response[0].strip()
        if header != "OK|SEARCH":
            print(f"Error: {header}")
            continue # Do another search

        results = [line.strip() for line in response[1:] if line.strip()]
        
        if not results:
            print(f"No matches found for '{search}'.")
            continue # Goes back to the top
        
        display_lines = []
        for i, u in enumerate(results, start=1):
            name = u.split("|")[0] if "|" in u else u
            status = u.split("|")[1] if "|" in u else "OFFLINE"
            
            if status == "ONLINE":
                display_lines.append(f"{i}) [green bold]{name:<20}● Online[/green bold]")
            else:
                display_lines.append(f"{i}) {name:<20}\t [white dim]○ Offline[/white dim]")

        panel_content = "\n".join(display_lines)
        console.print(Panel(panel_content, title=f"[bold blue]Matches for '{search}'[/bold blue]", subtitle="[dim]Select a number to start chat.[dim]", expand=False, border_style="cyan"))

        selection = input("\nSelect a number to chat, or Enter to search again: ").strip()
        
        if not selection:
            continue # Goes back to the top

        try:
            idx = int(selection)
            if 1 <= idx <= len(results):
                temp = results[idx - 1]
                peer_username = temp.split("|")[0] if "|" in temp else temp
                currentState = ClientStates.State.CHAT
                return # Successfully found a user, exit the search loop
            else:
                print("Invalid selection number.")
        except ValueError:
            print("Please enter a valid number.")

def handle_group_making(clientSocket: socket, username: str) -> None:
    """Create a group chat.

    Builds a `GROUP_CREATE` packet:
        GROUP_CREATE
        <group_name>
        <member_username>
        <member_username>
        ...

    The server returns `OK|GROUP_CREATED|<group_id>`.
    """
    global currentState

    group_name = input("Enter group name: ").strip()

    if not group_name:
        print("Group name cannot be empty.")
        return

    members = []
    print("Enter usernames to add to the group chat. Type '/exit' to stop:")
    while True:
        member = input("Add member: ").strip()
        if member == '/exit':
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

    currentState = ClientStates.State.ACCOUNT_MENU
    
def handle_group_list(clientSocket: socket, username: str) -> None:
    '''
    Makes a list of the groups that a user is in currently.
    '''

    global currentState
    global group_id
    global group_name

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
        cprint("You are not in any groups yet.", "red")
        input("Press enter to continue.")
        sys.stdout.write("\r" + " " * 100 + "\r")
        sys.stdout.flush()

        currentState = ClientStates.State.ACCOUNT_MENU

        return
    
    print("Your groups:")
    group_entries = []
    for i, (group_id, group_name) in enumerate(groups, start=1):
        group_entries.append(f"{i}) [bold]{group_name:<20}[/bold] [purple](ID: {group_id})[/purple]")

    if not group_entries:
        panel_content = "[italic white dim]No groups found.[/italic white dim]"
    else:
        panel_content = "\n".join(group_entries)

    console.print(Panel(panel_content, title="[bold cyan]Your Group Chats[/bold cyan]", subtitle="[dim]Select a number to to start chat[/dim]", expand=False,border_style="cyan",padding=(1, 2)))
    
    selection = input("\nOR Press Enter to go back.").strip()
    if not selection:
        currentState = ClientStates.State.ACCOUNT_MENU
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
    currentState = ClientStates.State.GROUP

def start_group_chat(clientSocket: socket, my_username: str, group_id: str, group_name: str):
    '''
    Allows the user to engage in a group chat with other accounts. Commands are given as follows:
    1.) /sendfile allows the user to send a file to another user (the file's absolute path is important here).
    2.) /add allows the user to add a member to the group.
    3.) /exit allows the user to exit the chat.
    '''

    global currentState

    send_message(clientSocket, f"{Protocol.initiate_protocol(14)}\n{group_id}\n\n")
    packet = receive_packet(clientSocket)

    if not packet:
        cprint("No response from server.", "red")
        return
    
    header = packet[0].strip()
    if header == "ERROR|NOT_IN_GROUP":
        cprint("You are not a member of this group.", "red")
        return
    if header == "ERROR|DB_ERROR":
        cprint("Database error.", "red")
        return
    if header != "OK|GROUP_HISTORY":
        cprint(f"Unexpected server message: {header}", "red")
        return
    
    chat_menu = (
        f"Now chatting with [green bold]{group_name}[/green bold].\n\n"
        "1.) [purple bold]/sendfile[/purple bold] [yellow]<absolute path>[/yellow]: Send a file.\n"
        "1.) [purple bold]/add[/purple bold] [yellow]<username>[/yellow]: Adds a member to the group.\n"
        "3.) [purple bold]/exit[/purple bold]: Leave the chat."
    )

    console.print(Panel(chat_menu, title="[bold cyan]Group Chat[/bold cyan]", expand=False, border_style="bright_magenta"))

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
            if kind in ("OK|GROUP_MESSAGE_SENT", "OK|GROUP_CLOSED", "OK|MEMBER_ADDED", "OK|GROUP_BLOB_NOTIFY_SENT"):
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

            elif kind == "GROUP_BLOB_OFFER" and len(incoming) >= 6:
                incoming_group_id = incoming[1].strip()
                blob_sender = incoming[2].strip()
                blob_host = incoming[3].strip()
                try:
                    blob_port = int(incoming[4].strip())
                except ValueError:
                    continue
                blob_filename = incoming[5].strip()

                if incoming_group_id == str(group_id):
                    sys.stdout.write("\r\033[K")
                    print(f"[File incoming in group from {blob_sender}: '{blob_filename}']")
                    reprint_prompt()
                    threading.Thread(
                        target=p2p.receive_blob,
                        args=(blob_host, blob_port, blob_filename),
                        daemon=True,
                    ).start()

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
                    currentState = ClientStates.State.ACCOUNT_MENU
                    break

                if msg.strip().startswith("/add "):
                    new_member = msg.strip()[len("/add "):].strip()
                    if new_member:
                        print(f"Adding member: {new_member}")
                        send_message(clientSocket, f"{Protocol.initiate_protocol(17)}\n{group_id}\n{new_member}\n\n")
                    sys.stdout.write("\ryou> ")
                    sys.stdout.flush()
                    continue

                if msg.strip().startswith("/sendfile "):
                    file_path = msg.strip()[len("/sendfile "):].strip()
                    if file_path:
                        print(f"Sending file to group: {file_path}")
                        p2p.send_group_blob(file_path, clientSocket, my_username, str(group_id))
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
                    else:
                        sys.stdout.write("\a") 
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

def close_program(clientSocket: socket) -> None:
    '''Disconnects the user from the socket.'''
    send_message(clientSocket, f"{Protocol.initiate_protocol(3)}\n\n")

    output = receive_message(clientSocket).strip()
    if output == "OK|BYE":
        cprint("You have successfully closed the program.", "green")
        clientSocket.close()
        quit()

    pass

def main():
    """Connect to the TCP server and start the UI state machine."""
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
    '''Send a TCP message to the server.'''
    clientSocket.sendall(message.encode())
    pass

# UDP equivalent of the send_message method. 
def send_message_udp(message: str, udpSocket: socket, ip: str, port: int) -> None:
    '''Send a UDP datagram (used for pings).'''
    udpSocket.sendto(message.encode(), (ip, port))
    pass

# Receives a message from the server.
def receive_message(clientSocket: socket) -> str:
    '''Receive a TCP message chunk (up to 1024 bytes).'''
    return clientSocket.recv(1024).decode()

# Much more elaborate variation of the receive_packet method,
# which receives the entire message in chunks rather than preemptively truncating it.
def receive_packet(clientSocket: socket) -> list:
    '''Receive a full \n\n-terminated packet and split it into lines.'''
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
    """Background UDP ping loop.

    Every `PING_TIME` seconds this sends:
        `PING|<username>`

    to the server's UDP port. The server uses this to time users out when they
    stop sending pings.
    """
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
