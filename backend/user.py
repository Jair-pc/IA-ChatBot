from flask_login import UserMixin, current_user
from backend.db import mysql  # Importe a instância do Flask-MySQLDB

class User(UserMixin):
    def __init__(self, user_id, username):
        self.id = user_id
        self.username = username

    @staticmethod
    def get(user_id):
        # Conecte-se ao banco de dados usando a instância do Flask-MySQLDB
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user_data = cur.fetchone()
        cur.close()

        if user_data:
            return User(user_id=user_data[0], username=user_data[1])
        else:
            return None

    @staticmethod
    def get_user_chats(user_id):
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM chats WHERE user_id = %s", (user_id,))
        chats = cur.fetchall()
        cur.close()
        return chats
