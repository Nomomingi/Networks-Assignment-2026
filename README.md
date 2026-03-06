# **Networks Assignment 1**

- Paul Kabulu
- Chandik Naidoo
- Makolela Shibambu 

This is our group's prototype of a instant messaging application, fully designed in python.


### **How to run the db**
1. Make sure you have mysql set up on your machine.
2. Run `make db` to initialise the schema.
3. Verify the tables were created by checking mysql workbench or via your terminal.
4. Populate the db with dummy data with the following command: `make seed`.


### **DB Python Setup**
1. Install the dependencies using the following command:
    ```bash
    make requirements
    ```
    **Note:** Make sure to be running a **unix based terminal** in order to be able to use make commands. Otherwise, you can watch a YouTube tutorial on the Windows set. 
2. Create a `.env` file to store environment variables using the following command:
```bash
make env
```
- The environment variables ensure that our secret info such as passwwords, api keys, etc are not accessible to the public or pushed to github.
- The `make env` command will not fill in your mysql password, so you should add that manually in the `.env` file. Also just verify that the `DB_USER` and `HOST` variables match your mysql host and user - the one you made during the mysql setup in CSC2001F or whenever you set it up.

3. Test that the db connection works by running the `db.py` file. If you ran the `seed.sql` file initially, you should see something like:
```bash
➜  nets git:(db-methods) ✗ python3 db.py
DB connection successful [(1, 'paul', 'pass123', 1, datetime.datetime(2026, 3, 2, 19, 17, 10)), (2, 'paulihno', '123pass', 1, datetime.datetime(2026, 3, 2, 19, 17, 10))]
➜  nets git:(db-methods) ✗ 
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
Generative AI was used to help with the chat formatting. Our initial chat simply used python's input funcion and print function to get user input and siplay it to stdout. That resulted in formatting issues whereby the stuff you were typing would disappear or the stuff you were typing would merge with recived text if you were typing when you recived a new text. So we got helped from Claude AI to fix that issue. It provided us with a much more sophisticated approach, which ultimately resolved the issue. Additionally, we were having problems with our chat. We had race conditions, which resulted the clients no longer recieving texts after texts were sent simultaneously. We used generative ai to fix and debug the issue. 