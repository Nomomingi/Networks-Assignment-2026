from socket import *
import threading 

clients = set()

def handle_client(connection, address):
    temp = connection.recv(1024).decode().split("\n")
    username, password = temp[0], temp[1]
    print("Username:\t", username, "\nPassword:\t", password)

def main():
    serverPort = 12000
    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.bind(('', serverPort))
    serverSocket.listen(2000)
    print("The server is up and running.")
    while True:
        connectionSocket, addr = serverSocket.accept()
        thread = threading.Thread(target = handle_client, args = (connectionSocket, addr))
        thread.start()
    
if __name__ == "__main__":
    main()