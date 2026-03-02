from socket import *

# This method creates a temporary user whose details will be compared to the details on the server.
def create_temp_user(username: str,  password: str) -> list:
    temp = [username, password]
    return temp

# Logs the given user to their account.
def log_in(clientSocket: socket) -> None:
    username = input("Please enter your username:\t")
    password  = input ("Please enter your password:\t")
    temp = create_temp_user(username, password)
    send_message(clientSocket, f"LOGIN|{temp[0]}\n{temp[1]}")

    text = receive_message(clientSocket)

    print(text)
    if text == "Would you like to make an account?[Y/n]:\t":
        confirmation = input()
        if confirmation.lower() == "y":
            # send confirmation to create account to server.
            pass

def main():
    try:
        serverName = 'localhost'
        serverPort = 12000
        clientSocket = socket(AF_INET, SOCK_STREAM)
        clientSocket.connect((serverName, serverPort))
        while True:
            print("Welcome to our chat app! Press:\n" \
            "1. Log-in/Sign-Up\n" \
            "2. Close Program")
            num = eval(input())
            if num == 1:
                log_in(clientSocket)
            elif num == 2:
                break
            else:
                continue
        clientSocket.close()
    except ConnectionRefusedError:
        print("The connection was refused.\nThe server may be offline.")

# Sends a message to the server for simplicity.
def send_message(clientSocket: socket, message: str) -> None:
    clientSocket.send(message.encode())
    pass

# Receives a message from the server.
def receive_message(clientSocket: socket) -> str:
    return clientSocket.recv(1024).decode()
    

if __name__ == "__main__":
    main()