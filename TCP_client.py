from socket import *

# This method creates a temporary user whose details will be compared to the details on the server.
def create_temp_user(username: str,  password: str) -> list:
    temp = [username, password]
    return temp

def main():
    serverName = 'localhost'
    serverPort = 12000
    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.connect((serverName, serverPort))
    username = input("Please enter your username:\n")
    password  = input ("Please enter your password:\t")
    temp = create_temp_user(username, password)
    clientSocket.send(f"{temp[0]}\n{temp[1]}".encode())
    clientSocket.close()

if __name__ == "__main__":
    main()