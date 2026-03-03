from dotenv import load_dotenv
import mysql.connector
import os

load_dotenv()

HOST = os.getenv("HOST")
USER = os.getenv("USER")
PASSWORD = os.getenv("PASSWORD")
DATABASE = os.getenv("DATABASE")
PORT = os.getenv("PORT")

class DB:
    def __init__(self, host=HOST, user=USER, password=PASSWORD, database=DATABASE, port=PORT):
        self.connection = mysql.connector.connect(
            host=os.getenv(host),
            user=os.getenv(user),
            password=os.getenv(password),
            database=os.getenv(database)
        )
        self.cursor = self.connection.cursor()

    def execute(self, query, params=None):
        self.cursor.execute(query, params)
        self.connection.commit()

    def fetchall(self):
        return self.cursor.fetchall()

    def close(self):
        self.cursor.close()
        self.connection.close()


db = DB(host=HOST, user=USER, password=PASSWORD, port=PORT, database=DATABASE)

#get all users

def get_all_users():
    db.execute("SELECT * FROM users")
    return db.fetchall()


def get_user_by_id(user_id):
    db.execute("SELECT * FROM Users WHERE user_id = %d", (user_id))
    return db.fetchall()

def create_user(username, user_password):
    db.execute("INSERT INTo Users (username, user_password) VALUES (%s, %s)", (username, user_password))



    

