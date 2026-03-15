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
            port=port,
            autocommit=True
        )

    def _cursor(self):
        """Return a brand-new cursor for every query.
        This is the key to avoiding stale reads: MySQL Connector cursors hold a
        server-side read-view handle that persists between execute() calls on the
        same cursor instance.  Creating a fresh cursor ensures each SELECT sees
        the latest committed data, even with autocommit=True."""
        return self.connection.cursor()

    # ------------------------------------------------------------------ users

    def create_user(self, username, user_password):
        # Check for duplicates with a fresh cursor so we see the latest rows.
        if self.get_user_by_username(username):
            raise ValueError("User already exists.")
        cursor = self._cursor()
        cursor.execute(
            "INSERT INTO Users (username, user_password) VALUES (%s, %s)",
            (username, user_password),
        )
        cursor.close()

    def login_user(self, username: str, password: str) -> bool:
        """Verify credentials. Returns True on success, False otherwise."""
        if not username or not password:
            return False
        cursor = self._cursor()
        cursor.execute(
            "SELECT user_password FROM Users WHERE username = %s", (username,)
        )
        row = cursor.fetchone()
        cursor.close()
        if not row:
            return False
        return password == row[0]

    def updated_logged_in_status(self, user_id, status: bool):
        cursor = self._cursor()
        cursor.execute(
            "UPDATE Users SET logged_in = %s WHERE user_id = %s", (status, user_id)
        )
        cursor.close()

    def get_all_users(self):
        cursor = self._cursor()
        cursor.execute("SELECT * FROM Users")
        rows = cursor.fetchall()
        cursor.close()
        return rows

    def get_user_by_id(self, user_id):
        cursor = self._cursor()
        cursor.execute("SELECT * FROM Users WHERE user_id = %s", (user_id,))
        row = cursor.fetchone()
        cursor.close()
        return row

    def get_user_by_username(self, username):
        cursor = self._cursor()
        cursor.execute(
            "SELECT user_id, username FROM Users WHERE username = %s", (username,)
        )
        row = cursor.fetchone()
        cursor.close()
        return row

    def search_users(self, query: str, limit: int = 10):
        like = f"%{query}%"
        cursor = self._cursor()
        cursor.execute(
            "SELECT username FROM Users WHERE username LIKE %s ORDER BY username ASC LIMIT %s",
            (like, limit),
        )
        rows = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return rows

    def get_group_members(self, group_id):
        cursor = self._cursor()
        cursor.execute(
            "SELECT * FROM GroupChatMembers WHERE group_id = %s", (group_id,)
        )
        rows = cursor.fetchall()
        cursor.close()
        return rows

    def delete_user(self, user_id, username):
        cursor = self._cursor()
        cursor.execute(
            "DELETE FROM Users WHERE user_id = %s OR username = %s", (user_id, username)
        )
        cursor.close()

    def get_logged_status(self, user_id):
        cursor = self._cursor()
        cursor.execute("SELECT logged_in FROM Users WHERE user_id = %s", (user_id,))
        row = cursor.fetchone()
        cursor.close()
        return row

    # --------------------------------------------------------------- messages

    def store_private_message(self, sender_id, receiver_id, message_text, blob: Blob = None, delivered: int = 0):
        if not blob and not message_text:
            raise ValueError("Either message text or file must be provided.")
        media_data = blob.convert_to_binary_data() if blob else None
        cursor = self._cursor()
        cursor.execute(
            "INSERT INTO PrivateMessages (sender_id, receiver_id, message_text, media, delivered) VALUES (%s, %s, %s, %s, %s)",
            (sender_id, receiver_id, message_text, media_data, delivered),
        )
        last_id = cursor.lastrowid
        cursor.close()
        return last_id

    def get_private_messages(self, user_a_id, user_b_id):
        cursor = self._cursor()
        cursor.execute(
            """
            SELECT u.username, pm.message_text, pm.sent_at
            FROM PrivateMessages pm
            JOIN Users u ON u.user_id = pm.sender_id
            WHERE (pm.sender_id = %s AND pm.receiver_id = %s)
               OR (pm.sender_id = %s AND pm.receiver_id = %s)
            ORDER BY pm.sent_at ASC
            """,
            (user_a_id, user_b_id, user_b_id, user_a_id),
        )
        rows = cursor.fetchall()
        cursor.close()
        return rows

    def get_contacts(self, user_id: int):
        cursor = self._cursor()
        cursor.execute(
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
        rows = cursor.fetchall()
        cursor.close()
        return rows

    def get_undelivered_messages(self, receiver_id):
        cursor = self._cursor()
        cursor.execute(
            """
            SELECT pm.message_id, u.username, pm.message_text
            FROM PrivateMessages pm
            JOIN Users u ON u.user_id = pm.sender_id
            WHERE pm.receiver_id = %s AND pm.delivered = 0
            ORDER BY pm.sent_at ASC
            """,
            (receiver_id,),
        )
        rows = cursor.fetchall()
        cursor.close()
        return rows

    def mark_pm_delivered(self, message_id):
        cursor = self._cursor()
        cursor.execute(
            "UPDATE PrivateMessages SET delivered = 1, delivered_at = NOW() WHERE message_id = %s",
            (message_id,),
        )
        cursor.close()

    def mark_pm_delivered_between(self, sender_id, receiver_id):
        cursor = self._cursor()
        cursor.execute(
            "UPDATE PrivateMessages SET delivered = 1, delivered_at = NOW() WHERE sender_id = %s AND receiver_id = %s AND delivered = 0",
            (sender_id, receiver_id),
        )
        cursor.close()
    
    def create_group(self, group_name: str, creator_id: int):
        cursor = self._cursor()
        cursor.execute( "INSERT INTO GroupChat (group_name, created_by) VALUES (%s, %s)", (group_name, creator_id),)
        group_id = cursor.lastrowid
        cursor.close()
    
        self.add_user_to_group(group_id, creator_id)
        return group_id
    
    def add_user_to_group(self, group_id: int, user_id: int):
        cursor = self._cursor()
        cursor.execute("INSERT INTO GroupChatMembers (group_id, user_id) VALUES (%s, %s)", (group_id, user_id),)
        cursor.close()
    
    def get_user_groups(self, user_id: int):
        cursor = self._cursor()
        cursor.execute(
            """
            SELECT gc.group_id, gc.group_name
            FROM GroupChat gc
            JOIN GroupChatMembers gcm ON gc.group_id = gcm.group_id
            WHERE gcm.user_id = %s
            ORDER BY gc.group_name ASC
            """,
            (user_id,),
        )
        rows = cursor.fetchall()
        cursor.close()
        return rows
    
    def store_group_message(self, group_id: int, sender_id: int, message_text: str, blob: Blob = None):
        if not blob and not message_text:
            raise ValueError("Either message text or file must be provided.")
        
        media_data = blob.convert_to_binary_data() if blob else None
        cursor = self._cursor()
        cursor.execute("INSERT INTO GroupMessages (group_id, sender_id, message_text, media) VALUES (%s, %s, %s, %s)", (group_id, sender_id, message_text, media_data),)
        message_id = cursor.lastrowid
        cursor.close()
        return message_id
    
    def get_group_messages(self, group_id: int):
        cursor = self._cursor()
        cursor.execute(
            """
            SELECT u.username, gm.message_text, gm.sent_at
            FROM GroupMessages gm
            JOIN Users u ON u.user_id = gm.sender_id
            WHERE gm.group_id = %s
            ORDER BY gm.sent_at ASC
            """,
            (group_id, ),
        )
        rows = cursor.fetchall()
        cursor.close()
        return rows
    
    def get_group_member_usernames(self, group_id: int):
        cursor = self._cursor()
        cursor.execute(
            """
            SELECT u.username
            FROM GroupChatMembers gcm
            JOIN Users u ON u.user_id = gcm.user_id
            WHERE gcm.group_id = %s
            ORDER BY u.username ASC
            """,
            (group_id, ),
        )
        rows = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return rows

    def is_user_in_group(self, group_id: int, user_id: int) -> bool:
        cursor = self._cursor()
        cursor.execute("SELECT 1 FROM GroupChatMembers WHERE group_id = %s AND user_id = %s", (group_id, user_id),)
        row = cursor.fetchone()
        cursor.close()
        return row is not None

    
    def close(self):
        try:
            self.connection.close()
        except Exception as e:
            print("Error closing connection:", e)
