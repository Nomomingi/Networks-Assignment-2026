from fileinput import filename

from dotenv import load_dotenv
import mysql.connector
import os

load_dotenv()

HOST = os.getenv("HOST")
USER = os.getenv("DB_USER")
PASSWORD = os.getenv("PASSWORD")
DATABASE = os.getenv("DATABASE")
PORT = os.getenv("PORT")

class Blob:
    def __init__(self, file_path):
        self.file_path = file_path
    
    def convert_to_binary_data(self):
        with open(self.file_path, 'rb') as file:
            binary_data = file.read()
        return binary_data

class DB:
    def __init__(self, host=HOST, user=USER, password=PASSWORD, database=DATABASE, port=PORT):
        self.connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port
        )
        self.cursor = self.connection.cursor()

    # user related methods
    def create_user(self, username, user_password):
        if (self.get_user_by_username(username)):
            raise ValueError("User already exists.")
        
        self.cursor.execute("INSERT INTO Users (username, user_password) VALUES (%s, %s)", (username, user_password))
        self.connection.commit()
    
    def login_user(self, username:str, password:str):
        """This method will handle user login and verify if the user exists, and if they do, verify whether the provided password matches the password in the db.
        Returns: 
            bool: Wether the info provided is true of false"""

        self.cursor.execute("SELECT username, user_password FROM Users WHERE username = %s", (username,))
        user_info = self.cursor.fetchone()

        if (username is None or not(username)):
            return False
        
        if (username and (username == user_info[0] and password == user_info[1])):
            return True
        return False


    def get_all_users(self):
        self.cursor.execute("SELECT * FROM Users")
        return self.cursor.fetchall()
    
    def get_user_by_id(self, user_id):
        self.cursor.execute("SELECT * FROM Users WHERE user_id = %s", (user_id,))
        return self.cursor.fetchone()

    def get_user_by_username(self, username):
        self.cursor.execute("Select user_id, username FROM Users WHERE username = %s", (username,))
        return self.cursor.fetchone()
    
    def get_group_members(self, group_id):
        self.cursor.execute("SELECT * FROM GroupChatMembers WHERE group_id = %s", (group_id,))
        return self.cursor.fetchmany()
    
    def delete_user(self, user_id, username):
        self.cursor.execute("DELETE FROM Users WHERE user_id = %s OR username = %s", (user_id, username))
        return self.connection.commit()
    
    def get_logged_status(self, user_id):
        # Check whether someone is logged in
        self.cursor.execute("SELECT logged_in from Users WHERE user_id = %s", (user_id,))
        return self.cursor.fetchone()

    # Message related methods

    def store_private_message(self, sender_id, receiver_id, message_text, blob:Blob=None):
        if (not (blob and message_text)):
                raise ValueError("Either message text or file must be provided.")
        self.cursor.execute("INSERT INTO PrivateMessages (sender_id, receiver_id, message_text) VALUES (%s, %s, %s)", (sender_id, receiver_id, message_text))
        if (blob):
            self.cursor.execute("INSERT INTO PrivateMessages (media) VALUES (%s)", (blob,))
        return self.connection.commit()

    def get_private_messages(self, sender_id, reciever_id):
        # this method will get private messages between two users, sender and reciever
        self.cursor.execute("SELECT message_text, sent_at, media FROM PrivateMessages WHERE sender_id = %s OR sender_id=%s", (sender_id, reciever_id))
        return self.cursor.fetchall()
    
    def get_contacts(self, user_id):
        # this method will get all the contacts of a user, which are the users they have sent messages to or received messages from
        self.cursor.execute("SELECT DISTINCT sender_id FROM PrivateMessages WHERE receiver_id = %s", (user_id,))
        sent_contacts = self.cursor.fetchall()
        self.cursor.execute("SELECT DISTINCT receiver_id FROM PrivateMessages WHERE sender_id = %s", (user_id,))
        received_contacts = self.cursor.fetchall()
        return set(sent_contacts + received_contacts)



