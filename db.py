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

        self.cursor.execute("SELECT user_password FROM Users WHERE username = %s", (username,))
        user_info = self.cursor.fetchone()

        if not user_info:
            return False

        if not username or not password:
            return False
        
        return password == user_info[0]

    def updated_logged_in_status(self, user_id, status:bool):
        self.cursor.execute("UPDATE Users SET logged_in = %s WHERE user_id = %s", (status, user_id))
        return self.connection.commit()

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
        if not blob and not message_text:
                raise ValueError("Either message text or file must be provided.")
        
        media_data = blob.convert_to_binary_data() if blob else None
        self.cursor.execute("INSERT INTO PrivateMessages (sender_id, receiver_id, message_text, media, delivered) VALUES (%s, %s, %s, %s, 0)", (sender_id, receiver_id, message_text, media_data))
        return self.connection.commit()

    def get_private_messages(self, user_a_id, user_b_id):
        # this method will get private messages between two users, sender and reciever
        self.cursor.execute("SELECT message_text, sent_at, media FROM PrivateMessages WHERE (sender_id = %s AND receiver_id = %s) OR (sender_id=%s and receiver_id = %s) ORDER BY sent_at ASC", (user_a_id, user_b_id, user_b_id, user_a_id))
        return self.cursor.fetchall()
    
    def get_contacts(self, user_id: int):
        self.cursor.execute(
            """
            SELECT DISTINCT u.user_id, u.username
            FROM PrivateMessages pm
            JOIN Users u
              ON u.user_id = CASE
                WHEN pm.sender_id = %s THEN pm.receiver_id
                ELSE pm.sender_id
              END
            WHERE pm.sender_id = %s OR pm.receiver_id = %s
            """,
            (user_id, user_id, user_id),
        )
        return self.cursor.fetchall()
    
    def get_undelivered_messages(self, receiver_id):
        self.cursor.execute(
            """
            SELECT pm.message_id, u.username, pm.message_text
            FROM PrivateMessages pm
            JOIN Users u
              ON u.user_id = pm.sender_id
            WHERE pm.receiver_id = %s AND pm.delivered = 0
            ORDER BY pm.sent_at ASC
            """,
            (receiver_id,)
        )
        return self.cursor.fetchall()
    
    def mark_pm_delivered(self, message_id):
        self.cursor.execute("UPDATE PrivateMessages SET delivered = 1, delivered_at = NOW() WHERE message_id = %s", (message_id,))
        self.connection.commit()
    
    def close(self):
        try:
            self.cursor.close()
        except:
            pass
        try:
            self.connection.close()
        except:
            pass


