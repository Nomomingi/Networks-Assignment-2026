from dotenv import load_dotenv
import mysql.connector
import os

load_dotenv()

HOST = os.getenv("HOST")
USER = os.getenv("DB_USER")
PASSWORD = os.getenv("PASSWORD")
DATABASE = os.getenv("DATABASE")
PORT = os.getenv("PORT")

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
        self.cursor.execute("INSERT INTO Users (username, user_password) VALUES (%s, %s)", (username, user_password))
        return self.connection.commit()
    
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



db = DB(host=HOST, user=USER, password=PASSWORD, port=PORT, database=DATABASE)

print("DB connection successful", db.get_all_users())


