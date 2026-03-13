from socket import *
import Protocol # Custom made, see Protocol.py
import threading
from db import DB
import time
import traceback

online_users = {} # A dictionary to store the online users, and their sockets as a value.
users_last_seen = {} # A dictionary to store when last they were seen on the server.
online_lock = threading.Lock()
active_chats = {}
chat_lock = threading.Lock()
active_groups = {}
group_lock = threading.Lock()
SLEEPY_TIME = 20 # Constant for the time taken for a user to sleep.

def _proto(num: int) -> str | None:
    try:
        return Protocol.initiate_protocol(num)
    except Exception:
        return None

# Handles one connected client. Each client is run in its own thread
def handle_client(connectionSocket: socket, address: tuple):
    username = None # Will store the username of the logged-in user for this connection
    db_local = DB()
    try:
        while True:
            temp = receive_packet(connectionSocket) # Reads the entire message from the client
            if not temp: # If client provides no response. connection terminated
                break

            if username:
                with online_lock:
                    if username in users_last_seen:
                        users_last_seen[username] = time.time()
    
            action = temp[0].strip() # Tells the server what action the user wants to perform
            
            if action == _proto(1): # LOGIN
                username = handle_login(connectionSocket, temp, username, db_local)

            elif action == _proto(2): #CREATE
                handle_account_creation(connectionSocket, temp, db_local)

            elif action == _proto(3): #CLOSE
                handle_program_close(connectionSocket)
                break # Stop handling this client
            elif action == _proto(4): #PRIVATE
                handle_private_message(connectionSocket, username, temp, db_local)

            elif action == _proto(5): #SEARCH
                handle_search(connectionSocket, username, temp, db_local)

            elif action == _proto(8): #OPEN_CHAT
                handle_open_chat(connectionSocket, username, temp, db_local)

            elif action == _proto(9): #CLOSE_CHAT
                handle_close_chat(connectionSocket, username, temp)

            elif action == _proto(6): #CoNTACTS - People who you've chatted with
                handle_get_contacts(connectionSocket, username, db_local)

            elif action == _proto(10): #SEND_BLOB - relay ngrok address to recipient
                handle_send_blob(connectionSocket, username, temp)

            elif action == _proto(12):
                handle_group_create(connectionSocket, username, temp, db_local)
            
            elif action == _proto(13):
                handle_group_list(connectionSocket, username, db_local)
            
            elif action == _proto(14):
                handle_group_open(connectionSocket, username, temp, db_local)
            
            elif action == _proto(15):
                handle_group_message(connectionSocket, username, temp, db_local)
            
            elif action == _proto(16):
                handle_group_close(connectionSocket, username, temp)
            elif action == _proto(17):
                handle_group_add_member(connectionSocket, username, temp, db_local)
            else:
                send_message(connectionSocket, "ERROR|UNKNOWN_ACTION\n\n") # Action isn't recognised
    except Exception as e:
        traceback.print_exc()
        try:
            send_message(connectionSocket, "ERROR|SERVER_EXCEPTION\n\n")
        except:
            pass
    finally:
        if username:
            with online_lock:
                if online_users.get(username) is connectionSocket:
                    del online_users[username]
            with chat_lock:
                if username in active_chats:
                    del active_chats[username]
            with group_lock:
                if username in active_groups:
                    del active_groups[username]
        try:
            db_local.close()
        except:
            pass
        connectionSocket.close() # Close the connection when done

# Handles login requests. 
def handle_login(connectionSocket: socket, temp: list, current_user: str, db_local: DB):
    if len(temp) < 3:
        send_message(connectionSocket, "ERROR|INVALID_LOGIN_FORMAT\n\n")
        return current_user
    
    u = temp[1].strip()
    p = temp[2].strip()

    if not u or not p:
        send_message(connectionSocket, "ERROR|INVALID_CREDENTIALS\n\n")
        return current_user
    
    try:
        ok = db_local.login_user(u, p)
    except Exception as e:
        print("OPEN_CHAT error:", e)
        send_message(connectionSocket, "ERROR|DB_ERROR\n\n")
        return current_user
    
    if not ok:
        send_message(connectionSocket, "ERROR|LOGIN_FAILED\n\n")
        return current_user
    
    with online_lock:
        online_users[u] = connectionSocket
        users_last_seen[u] = time.time() # The current time.
    
    send_message(connectionSocket, "OK|LOGIN_SUCCESS\n\n")
    return u

def handle_open_chat(connectionSocket: socket, username: str | None, temp: list, db_local: DB):
    if not username:
        send_message(connectionSocket, "ERROR|NOT_LOGGED_IN\n\n")
        return
    if len(temp) < 2:
        send_message(connectionSocket, "ERROR|INVALID_OPEN_CHAT_FORMAT\n\n")
        return

    peer_username = temp[1].strip()
    if not peer_username:
        send_message(connectionSocket, "ERROR|INVALID_OPEN_CHAT_FORMAT\n\n")
        return

    try:
        user_row = db_local.get_user_by_username(username)
        peer_row = db_local.get_user_by_username(peer_username)
        if not user_row or not peer_row:
            send_message(connectionSocket, "ERROR|NO_SUCH_USER\n\n")
            return

        user_id = user_row[0]
        peer_id = peer_row[0]

        with chat_lock:
            active_chats[username] = peer_username

        history = db_local.get_private_messages(user_id, peer_id)

        lines = ["OK|CHAT_HISTORY"]
        for sender_name, message_text, sent_at in history:
            lines.append(f"{sender_name}|{message_text}|{sent_at}")
        send_message(connectionSocket, "\n".join(lines) + "\n\n")

        db_local.mark_pm_delivered_between(peer_id, user_id)
    except Exception:
        send_message(connectionSocket, "ERROR|DB_ERROR\n\n")

def handle_close_chat(connectionSocket: socket, username: str | None, temp: list):
    if not username:
        send_message(connectionSocket, "ERROR|NOT_LOGGED_IN\n\n")
        return

    with chat_lock:
        if username in active_chats:
            del active_chats[username]
    send_message(connectionSocket, "OK|CHAT_CLOSED\n\n")

def handle_get_contacts(connectionSocket: socket, username: str | None, db_local: DB):
    if not username:
        send_message(connectionSocket, "ERROR|NOT_LOGGED_IN\n\n")
        return

    try:
        user_row = db_local.get_user_by_username(username)
        if not user_row:
            send_message(connectionSocket, "ERROR|USER_NOT_FOUND\n\n")
            return
        user_id = user_row[0]

        contacts = db_local.get_contacts(user_id)
    except Exception:
        send_message(connectionSocket, "ERROR|DB_ERROR\n\n")
        return

    if not contacts:
        send_message(connectionSocket, "OK|CONTACTS\n\n")
        return

    lines = ["OK|CONTACTS"]
    for _contact_id, contact_username in contacts:
        lines.append(str(contact_username))
    send_message(connectionSocket, "\n".join(lines) + "\n\n")

def handle_search(connectionSocket: socket, username: str | None, temp: list, db_local: DB):
    if not username:
        send_message(connectionSocket, "ERROR|NOT_LOGGED_IN\n\n")
        return

    if len(temp) < 2:
        send_message(connectionSocket, "ERROR|INVALID_SEARCH_FORMAT\n\n")
        return

    query = temp[1].strip()
    if not query:
        send_message(connectionSocket, "ERROR|INVALID_SEARCH_FORMAT\n\n")
        return

    try:
        results = db_local.search_users(query)
    except Exception:
        send_message(connectionSocket, "ERROR|DB_ERROR\n\n")
        return

    lines = ["OK|SEARCH"]
    for u in results:
        lines.append(str(u))
    send_message(connectionSocket, "\n".join(lines) + "\n\n")

def handle_account_creation(connectionSocket: socket, temp: list, db_local: DB):
    if len(temp) < 3:
        send_message(connectionSocket, "ERROR|INVALID_CREATE_FORMAT\n\n")
        return
                
    new_user = temp[1].strip()
    new_password = temp[2].strip()

    if not new_user or not new_password:
        send_message(connectionSocket, "ERROR|INVALID_CREDENTIALS\n\n")
        return
    try:
        db_local.create_user(new_user, new_password)
        send_message(connectionSocket, "OK|SIGNUP_SUCCESSFUL\n\n")
    except Exception:
        send_message(connectionSocket, "ERROR|USER_ALREADY_EXISTS\n\n")

# This will be much more important later.
def handle_program_close(connectionSocket: socket):
    send_message(connectionSocket, "OK|BYE\n\n")

def handle_private_message(connectionSocket: socket, sender_username: str | None, temp: list, db_local: DB):
    if not sender_username:
        send_message(connectionSocket, "ERROR|NOT_LOGGED_IN\n\n")
        return
    
    if len(temp) < 3:
        send_message(connectionSocket, "ERROR|INVALID_PRIVATE_FORMAT\n\n")
        return

    receiver_username = temp[1].strip()
    message_text = temp[2].strip()
    if not receiver_username or not message_text:
        send_message(connectionSocket, "ERROR|INVALID_PRIVATE_FORMAT\n\n")
        return
    
    try:
        sender_info = db_local.get_user_by_username(sender_username)
        receiver_info = db_local.get_user_by_username(receiver_username)
        if not receiver_info:
            send_message(connectionSocket, "ERROR|NO_SUCH_USER\n\n")
            return
        if not sender_info:
            send_message(connectionSocket, "ERROR|SENDER_NOT_FOUND\n\n")
            return
        sender_id = sender_info[0]
        receiver_id = receiver_info[0]

        message_id = db_local.store_private_message(sender_id, receiver_id, message_text, delivered=0)

        with online_lock:
            receiver_socket = online_users.get(receiver_username)
        should_push = False
        with chat_lock:
            should_push = active_chats.get(receiver_username) == sender_username

        if receiver_socket and should_push:
            send_message(receiver_socket, f"INCOMING_PRIVATE\n{sender_username}\n{message_text}\n\n")
            db_local.mark_pm_delivered(message_id)
            send_message(connectionSocket, "OK|MESSAGE_SENT\n\n")
        else:
            send_message(connectionSocket, "OK|PRIVATE_STORED\n\n")
    except Exception:
        send_message(connectionSocket, "ERROR|DB_ERROR\n\n")

def handle_group_create(connectionSocket: socket, username: str | None, temp: list, db_local: DB):
    if not username:
        send_message(connectionSocket, "ERROR|NOT_LOGGED_IN\n\n")
        return
    
    if len(temp) < 2:
        send_message(connectionSocket, "ERROR|INVALID_GROUP_CREATE_FORMAT\n\n")
        return
    
    group_name = temp[1].strip()
    member_usernames = [name.strip() for name in temp[2: ] if name.strip()]

    if not group_name:
        send_message(connectionSocket, "ERROR|INVALID_GROUP_NAME\n\n")
        return
    
    try:
        creator_row = db_local.get_user_by_username(username)
        if not creator_row:
            send_message(connectionSocket, "ERROR|USER_NOT_FOUND\n\n")
            return
        creator_id = creator_row[0]
        group_id = db_local.create_group(group_name, creator_id)

        added_members = []
        for member_username in member_usernames:
            member_row = db_local.get_user_by_username(member_username)
            if member_row:
                member_id = member_row[0]
                try:
                    db_local.add_user_to_group(group_id, member_id)
                    added_members.append(member_username)
                except Exception:
                    pass
        send_message(connectionSocket, f"OK|GROUP_CREATED|{group_id}\n\n")
    except Exception:
        send_message(connectionSocket, "ERROR|DB_ERROR\n\n")

def handle_group_list(connectionSocket: socket, username: str | None, db_local: DB):
    if not username:
        send_message(connectionSocket, "ERROR|NOT_LOGGED_IN\n\n")
        return
    
    try:
        user_row = db_local.get_user_by_username(username)
        if not user_row:
            send_message(connectionSocket, "ERROR|USER_NOT_FOUND\n\n")
            return
        
        user_id = user_row[0]
        groups = db_local.get_user_groups(user_id)

        lines = ["OK|GROUPS"]
        for group_id, group_name in groups:
            lines.append(f"{group_id}|{group_name}")

        send_message(connectionSocket, "\n".join(lines) + "\n\n")

    except Exception:
        send_message(connectionSocket, "ERROR|DB_ERROR\n\n")
         
def handle_group_open(connectionSocket: socket, username: str | None, temp: list, db_local: DB):
    if not username:
        send_message(connectionSocket, "ERROR|NOT_LOGGED_IN\n\n")
        return
    
    if len(temp) < 2:
        send_message(connectionSocket, "ERROR|INVALID_GROUP_OPEN_FORMAT\n\n")
        return
    
    try:
        group_id = int(temp[1].strip())
    except ValueError:
        send_message(connectionSocket, "ERROR|INVALID_GROUP_ID\n\n")
        return
    
    try:
        user_row = db_local.get_user_by_username(username)
        if not user_row:
            send_message(connectionSocket, "ERROR|USER_NOT_FOUND\n\n")
            return
        
        user_id = user_row[0]
        if not db_local.is_user_in_group(group_id, user_id):
            send_message(connectionSocket, "ERROR|NOT_IN_GROUP\n\n")
            return
        
        with group_lock:
            active_groups[username] = group_id
        history = db_local.get_group_messages(group_id)
        lines = ["OK|GROUP_HISTORY"]
        for sender_username, message_text, sent_at in history:
            lines.append(f"{sender_username}|{message_text}|{sent_at}")
        send_message(connectionSocket, "\n".join(lines) + "\n\n")

    except Exception:
        send_message(connectionSocket, "ERROR|DB_ERROR\n\n")
    
def handle_group_message(connectionSocket: socket, username: str | None, temp: list, db_local: DB):
    if not username:
        send_message(connectionSocket, "ERROR|NOT_LOGGED_IN\n\n")
        return
    
    if len(temp) < 3:
        send_message(connectionSocket, "ERROR|INVALID_GROUP_MESSAGE_FORMAT\n\n")
        return
    
    try:
        group_id = int(temp[1].strip())
    except ValueError:
        send_message(connectionSocket, "ERROR|INVALID_GROUP_ID\n\n")
        return
    
    message_text = temp[2].strip()
    if not message_text:
        send_message(connectionSocket, "ERROR|EMPTY_GROUP_MESSAGE\n\n")
        return
    
    try:
        sender_row = db_local.get_user_by_username(username)
        if not sender_row:
            send_message(connectionSocket, "ERROR|USER_NOT_FOUND\n\n")
            return
        
        sender_id = sender_row[0]

        if not db_local.is_user_in_group(group_id, sender_id):
            send_message(connectionSocket, "ERROR|NOT_IN_GROUP\n\n")
            return
        
        db_local.store_group_message(group_id, sender_id, message_text)
        member_rows = db_local.get_group_members(group_id)

        recipients = []
        with group_lock:
            for _group_id, member_user_id, *_ in member_rows:
                member_user = db_local.get_user_by_id(member_user_id)
                if not member_user:
                    continue
                member_username = member_user[1]

                if member_username == username:
                    continue

                if active_groups.get(member_username) == group_id:
                    recipients.append(member_username)
        
        with online_lock:
            recipient_sockets = [online_users[member_username] for member_username in recipients if member_username in online_users]
        
        for sock in recipient_sockets:
            send_message(sock, f"INCOMING_GROUP\n{group_id}\n{username}\n{message_text}\n\n")
        
        send_message(connectionSocket, "OK|GROUP_MESSAGE_SENT\n\n")

    except Exception:
        send_message(connectionSocket, "ERROR|DB_ERROR\n\n")

def handle_group_close(connectionSocket: socket, username: str | None, temp: list):
    if not username:
        send_message(connectionSocket, "ERROR|NOT_LOGGED_IN\n\n")
        return
    
    with group_lock:
        if username in active_groups:
            del active_groups[username]
    
    send_message(connectionSocket, "OK|GROUP_CLOSED\n\n")

def handle_group_add_member(connectionSocket: socket, username: str | None, temp: list, db_local: DB):
    if not username:
        send_message(connectionSocket, "ERROR|NOT_LOGGED_IN\n\n")
        return

    if len(temp) < 3:
        send_message(connectionSocket, "ERROR|INVALID_GROUP_ADD_MEMBER_FORMAT\n\n")
        return

    try:
        group_id = int(temp[1].strip())
    except ValueError:
        send_message(connectionSocket, "ERROR|INVALID_GROUP_ID\n\n")
        return

    member_username = temp[2].strip()
    if not member_username:
        send_message(connectionSocket, "ERROR|INVALID_GROUP_ADD_MEMBER_FORMAT\n\n")
        return

    try:
        requester_row = db_local.get_user_by_username(username)
        if not requester_row:
            send_message(connectionSocket, "ERROR|USER_NOT_FOUND\n\n")
            return

        requester_id = requester_row[0]
        if not db_local.is_user_in_group(group_id, requester_id):
            send_message(connectionSocket, "ERROR|NOT_IN_GROUP\n\n")
            return

        member_row = db_local.get_user_by_username(member_username)
        if not member_row:
            send_message(connectionSocket, "ERROR|NO_SUCH_USER\n\n")
            return

        member_id = member_row[0]
        if db_local.is_user_in_group(group_id, member_id):
            send_message(connectionSocket, "ERROR|ALREADY_IN_GROUP\n\n")
            return

        db_local.add_user_to_group(group_id, member_id)
        send_message(connectionSocket, "OK|MEMBER_ADDED\n\n")
    except Exception:
        send_message(connectionSocket, "ERROR|DB_ERROR\n\n")

def handle_send_blob(connectionSocket: socket, sender_username: str | None, temp: list):
    """
    Pure signaling relay — the server never sees file data.
    Reads the sender's public ngrok host/port and pushes a BLOB_OFFER to the
    recipient's already-open main TCP socket so they can connect directly.

    Expected packet from sender:
        SEND_BLOB
        <sender_username>
        <peer_username>
        <filename>
        <ngrok_host>          e.g. 0.tcp.eu.ngrok.io
        <ngrok_port>          e.g. 12345
    """
    if not sender_username:
        send_message(connectionSocket, "ERROR|NOT_LOGGED_IN\n\n")
        return

    if len(temp) < 6:
        send_message(connectionSocket, "ERROR|INVALID_BLOB_FORMAT\n\n")
        return

    peer_username = temp[2].strip()
    filename      = temp[3].strip()
    ngrok_host    = temp[4].strip()
    ngrok_port    = temp[5].strip()

    if not peer_username or not filename or not ngrok_host or not ngrok_port:
        send_message(connectionSocket, "ERROR|INVALID_BLOB_FORMAT\n\n")
        return

    with online_lock:
        recipient_socket = online_users.get(peer_username)

    if not recipient_socket:
        send_message(connectionSocket, "ERROR|PEER_OFFLINE\n\n")
        return

    try:
        send_message(recipient_socket,
                     f"BLOB_OFFER\n{sender_username}\n{ngrok_host}\n{ngrok_port}\n{filename}\n\n")
        send_message(connectionSocket, "OK|BLOB_NOTIFY_SENT\n\n")
    except Exception:
        send_message(connectionSocket, "ERROR|NOTIFY_FAILED\n\n")

# This is largely for the sake of achieving the 'Ping' effect with our chats.
# The good thing about this entire scenario is that we only need to store the effect as:
# PING|Username
def udp_server() -> None:
    serverPort = 14400 
    serverSocket = socket(AF_INET, SOCK_DGRAM)
    serverSocket.bind(('0.0.0.0', serverPort))
    print("The UDP server is up and running.")
    while True:
        temp, address = serverSocket.recvfrom(1024)
        message = temp.decode().strip().split("|")
        if message[0] == Protocol.initiate_protocol(7): # PING
            username = message[1]
            with online_lock:
                if username in users_last_seen:
                    users_last_seen[username] = time.time()

# Logs users who haven't sent out a ping to the UDP server out of the TCP server.
def check_sleepy_accounts():
    print("The sleepy thread is running.")
    while True:
        time.sleep(SLEEPY_TIME)
        current = time.time()
        with online_lock:
            for user in list(users_last_seen.keys()):
                if (current - users_last_seen[user]) >= SLEEPY_TIME:
                    # TODO: Print timeout message for the user.
                    del users_last_seen[user]
                    if user in online_users:
                        del online_users[user]

def main():
    serverPort = 14532
    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.bind(('0.0.0.0', serverPort))
    serverSocket.listen(5)
    print("The TCP server is up and running.")

    #udpThread = threading.Thread(target = udp_server, daemon = True) # UDP Thread
    #sleepyThread = threading.Thread(target = check_sleepy_accounts, daemon = True) # The sleep checker
    #udpThread.start()
    #sleepyThread.start()


    while True:
        connectionSocket, addr = serverSocket.accept()
        tcpThread = threading.Thread(target = handle_client, args = (connectionSocket, addr))
        tcpThread.start()
    
# Sends a message to the client for simplicity.
def send_message(connectionSocket: socket, message: str) -> None:
    connectionSocket.sendall(message.encode())

# Receives a message from the client.
def receive_message(connectionSocket: socket) -> str:
    return connectionSocket.recv(1024).decode()

# 
def receive_packet(connectionSocket: socket) -> list:
    data = ""
    while True:
        chunk = connectionSocket.recv(1024).decode(errors= "ignore")

        if not chunk:
            return []
        data += chunk

        if "\n\n" in data: 
            break
    packet = data.split("\n\n")[0]
    return packet.split("\n")
    
if __name__ == "__main__":
    main()