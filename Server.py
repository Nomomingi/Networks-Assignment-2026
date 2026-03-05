from socket import *
import Protocol # Custom made, see Protocol.py
import threading
from db import DB
import time

online_users = {} # A dictionary to store the online users, and their sockets as a value.
users_last_seen = {} # A dictionary to store when last they were seen on the server.
online_lock = threading.Lock()
SLEEPY_TIME = 20 # Constant for the time taken for a user to sleep.

# Handles one connected client. Each client is run in its own thread
def handle_client(connectionSocket: socket, address: tuple):
    username = None # Will store the username of the logged-in user for this connection
    db_local = DB()
    try:
        while True:
            temp = receive_packet(connectionSocket) # Reads the entire message from the client
            if not temp: # If client provides no response. connection terminated
                break
    
            action = temp[0].strip() # Tells the server what action the user wants to perform
            
            if action == Protocol.initiate_protocol(1): # LOGIN
                username = handle_login(connectionSocket, temp, username, db_local)

            elif action == Protocol.initiate_protocol(2): #CREATE
                handle_account_creation(connectionSocket, temp, db_local)

            elif action == Protocol.initiate_protocol(3): #CLOSE
                handle_program_close(connectionSocket)
                break # Stop handling this client
            elif action == Protocol.initiate_protocol(4): #PRIVATE
                handle_private_message(connectionSocket, username, temp, db_local)

            elif action == Protocol.initiate_protocol(6): #CoNTACTS - People who you've chatted with
                handle_get_contacts(connectionSocket, username, db_local)

            else:
                send_message(connectionSocket, "ERROR|UNKNOWN_ACTION\n\n") # Action isn't recognised
    except Exception as e:
        try:
            send_message(connectionSocket, "ERROR|SERVER_EXCEPTION\n\n")
        except:
            pass
    finally:
        if username:
            with online_lock:
                if online_users.get(username) is connectionSocket:
                    del online_users[username]
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
    except Exception:
        send_message(connectionSocket, "ERROR|DB_ERROR\n\n")
        return current_user
    
    if not ok:
        send_message(connectionSocket, "ERROR|LOGIN_FAILED\n\n")
        return current_user
    
    with online_lock:
        old = online_users.get(u)
        online_users[u] = connectionSocket
        users_last_seen[u] = time.time() # The current time.
    
    send_message(connectionSocket, "OK|LOGIN_SUCCESS\n\n")

    try:
        user_info = db_local.get_user_by_username(u)
        if user_info:
            user_id = user_info[0]
            undelivered = db_local.get_undelivered_messages(user_id)

            for message_id, sender_username, message_text in undelivered:
                send_message(connectionSocket, f"INCOMING_PRIVATE\n{sender_username}\n{message_text}\n\n")
                db_local.mark_pm_delivered(message_id)
    except Exception:
        pass
    return u

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

        with online_lock:
            receiver_socket = online_users.get(receiver_username)
        if receiver_socket:
            send_message(receiver_socket, f"INCOMING_PRIVATE\n{sender_username}\n{message_text}\n\n")
            send_message(connectionSocket, "OK|MESSAGE_SENT\n\n")
        else:
            db_local.store_private_message(sender_id, receiver_id, message_text)
            send_message(connectionSocket, "OK|PRIVATE_STORED\n\n")
    except Exception:
        send_message(connectionSocket, "ERROR|DB_ERROR\n\n")

def main():
    serverPort = 12000
    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.bind(('0.0.0.0', serverPort))
    serverSocket.listen(5)
    print("The TCP server is up and running.")

    udpThread = threading.Thread(target = udp_server, daemon = True) # UDP Thread
    sleepyThread = threading.Thread(target = check_sleepy_accounts, daemon = True) # The sleep checker
    udpThread.start()
    sleepyThread.start()


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