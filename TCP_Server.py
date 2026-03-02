from socket import *
import threading 

accounts = dict() # A dictionary of the accounts present in the textfile.

def handle_client(connectionSocket: socket, address: tuple):
    temp = connectionSocket.recv(1024).decode().split("\n")
    username, password = temp[0], temp[1]

    # Checks if the username exists or not.
    try:
        if accounts[username] == password:
            # Allow access to the account.
            connectionSocket.sendall("Your account exists.".encode())
        else:
            connectionSocket.sendall("Wrong password.".encode())
    except KeyError:
        # Ask if user would like to make an account.
        connectionSocket.sendall("Would you like to make an account?[Y/n]:\t".encode())
        pass

    finally:
        connectionSocket.close()

# Loads the accounts from the accounts.txt.
def load_accounts(txt: str = "accounts.txt") -> None:
    accounts.clear()
    with open(txt, 'r') as f:
        for line in f:
            username, password = line.split(",")
            accounts[username] = password

# Appends an account into accounts.txt.
def write_account(username: str, password: str) -> None:
    load_accounts() #HACK: May remove.
    if username not in accounts:
        with open("accounts.txt", "a") as f:
            f.write("f:{username},{password}\n")

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
    connectionSocket.send(message.encode())
    pass

# Receives a message from the client.
def receive_message(connectionSocket: socket) -> str:
    return connectionSocket.recv(1024).decode()
    
if __name__ == "__main__":
    main()