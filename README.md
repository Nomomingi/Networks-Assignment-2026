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

### **How to get an ngrok auth token**
1. Install ngrok with the following command:
- Mac OS
 - Install homebrew:
 ```bash
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
 ```
 - Install ngrok
 ```bash
        brew install ngrok/ngrok/ngrok
 ```
 - Verify that it was installed:
 ```bash
        ngrok --version
 ```

- windows
 - Got to the [ngrok](https://ngrok.com/download/windows) official site and follow download instructions

After installing ngrok, login to your account using the following command:
```bash
        ngrok config add-authtoken <your-auth-token>
```

- Get your auth token from: https://dashboard.ngrok.com/login, under getting started > your auth token.

### **How to run the sever**
TODO: Add instructions for running the server


### **How to run the client**
Run the following command:
```make client
```
or alternatively,
```python3 Client.py
```


### **General program workflow**
1. Login/Create an account.
2. Check contacts (people you've chatted withj) or search for an account.
3. Select the number of the account you want to chat with.
4. To exit the chat, type `/exit`.

