# **Networks Assignment 1**

- Paul Kabulu
- Chandik Naidoo
- Makolela Shibambu 

This is the repo for the complete source code of our Networks Assignment 1.


### **Prerequisites:**
- Make sure you have mysql set up on your machine.
- Make sure you have ngrok installed on your machine.

### **Steps to set up the application**
**Note:** Make sure you're running a **unix based terminal** in order to be able to use make commands. Otherwise, you can watch a YouTube tutorial on the Windows set. Additionally, terminal formatting requires a unix based terminal.

1. Install the required dependencies using `make requirements`.
2. Create a `.env` file to store environment variables using the following command (for the tutors, we'll attach our `.env` file with this assignment):

```bash
make env
```
- Update the `.env` file with your mysql username & password, and your ngrok authtoken.
- The environment variables ensure that our secret info such as passwwords, api keys, etc are not accessible to the public or pushed to github.
- The `make env` command will not fill in your mysql password, so you should add that manually in the `.env` file. Also just verify that the `DB_USER` and `HOST` variables match your mysql host and user - the one you made during the mysql setup in CSC2001F or whenever you set it up.
3. Run `make db` to initialise the schema.
4. (optionally) run `make seed` to populate the db with dummy data.
5. Test that the db was created by running the following command in your terminal:
```bash
        source .env && mysql -u $DB_USER -p -e "USE chat_app; SHOW TABLES;"
```

### **How to run the sever**
The TCP server runs on localhost. We'll use ngrok for port forwarding so that the public has access to our localhost server. So before you begin, amke sure you have ngrok installed.

Go to the [ngrok website](https://ngrok.com/) and sign up for an account. Then, follow the instructions to install ngrok on your machine.

1. Run the server and ngrok with `make server`.
2. The server will start on port 14532 and ngrok will create a tunnel to expose it to the internet.
3. Copy the ngrok URL and use it in the client to connect to the server. The url should look something like this: `tcp://0.tcp.ngrok.io:12345`. In the `Client.py` file, nagiavte to the `main` funtion definition and update the `serverName` variable to  `<n>.tcp.<region>.ngrok.io` where `<n>` is the number in the url and `<region>` is the region of the url. Set the `serverPort` variable to the port number in the url - the nnumber after the colon.
4. Run the client with `python3 Client.py`.


### **General program workflow**
1. Login/Create an account.
2. Check contacts (people you've chatted withj) or search for an account.
3. Select the number of the account you want to chat with.
4. To exit the chat, type `/exit`.

### **GEneral notes**
THe program is currently incomplete. There are bugs, missing features, and some inconsistencies that need to be adressed. All of these issues will be fixed in the next phase. For the prototype, our MVP was to get private chats working. Other stuff such as group chats and file sharing will follow in the final phase.

### **Acknowledgements**
st