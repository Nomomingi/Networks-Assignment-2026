from socket import *
import Protocol # Custom made, see Protocol.py
import threading 

accounts = dict() # A dictionary of the accounts present in the textfile.
account_lock = threading.Lock()


def handle_client(connectionSocket: socket, address: tuple):
    username = None
    try:
        while True:
            temp = receive_packet(connectionSocket)
            if not temp:
                break
    
            action = temp[0].strip()
            if action == Protocol.initiate_protocol(1):
                username = handle_login(connectionSocket, temp, username)

            elif action == Protocol.initiate_protocol(2):
                handle_account_creation(connectionSocket, temp)

            elif action == Protocol.initiate_protocol(3):
                handle_program_close(connectionSocket)
                break

            else:
                send_message(connectionSocket, "ERROR|UNKNOWN_ACTION\n\n")
    except Exception as e:
        try:
            send_message(connectionSocket, "ERROR|SERVER_EXCEPTION\n\n")
        except:
            pass
    finally:
        connectionSocket.close()

def handle_login(connectionSocket: socket, temp: list, current_user: str):
    if len(temp) < 3:
        send_message(connectionSocket, "ERROR|INVALID_LOGIN_FORMAT\n\n")
        return current_user
    
    u = temp[1].strip()
    p = temp[2].strip()

    load_accounts()

    if u in accounts and accounts[u].strip() == p:
        send_message(connectionSocket, "OK|LOGIN_SUCCESS\n\n")
        return u
    if u in accounts:
        send_message(connectionSocket, "ERROR|INCORRECT_PASSWORD\n\n")
    else:
        send_message(connectionSocket, "ERROR|NO_SUCH_USER|SIGNUP_REQUIRED\n\n")
    
    return current_user

def handle_account_creation(connectionSocket: socket, temp: list):
    if len(temp) < 3:
        send_message(connectionSocket, "ERROR|INVALID_CREATE_FORMAT\n\n")
        return
                
    new_user = temp[1].strip()
    new_password = temp[2].strip()

    with account_lock:
        load_accounts()
        if new_user in accounts:
            send_message(connectionSocket, "ERROR|USER_ALREADY_EXISTS\n\n")
            return
        write_account(new_user, new_password)
        send_message(connectionSocket, "OK|SIGNUP_SUCCESSFUL\n\n")


# This will be much more important later.
def handle_program_close(connectionSocket: socket):
    send_message(connectionSocket, "OK|BYE\n\n")

# Loads the accounts from the accounts.txt.
def load_accounts(txt: str = "accounts.txt") -> None:
    accounts.clear()
    with open(txt, 'r') as f:
        for line in f:
            if not line.strip():
                continue
            username, password = line.strip().split(",",1)
            accounts[username] = password

# Appends an account into accounts.txt.
def write_account(username: str, password: str) -> None:
    load_accounts() #HACK: May remove.
    if username not in accounts:
        with open("accounts.txt", "a") as f:
            f.write(f"{username},{password}\n")
        accounts[username] = password

def main():
    serverPort = 12000
    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.bind(('', serverPort))
    serverSocket.listen(5)
    load_accounts() # Loading the accounts from accounts.txt.
    print("The server is up and running.")
    while True:
        connectionSocket, addr = serverSocket.accept()
        thread = threading.Thread(target = handle_client, args = (connectionSocket, addr))
        thread.start()
    
# Sends a message to the client for simplicity.
def send_message(connectionSocket: socket, message: str) -> None:
    connectionSocket.sendall(message.encode())

# Receives a message from the client.
def receive_message(connectionSocket: socket) -> str:
    return connectionSocket.recv(1024).decode()

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