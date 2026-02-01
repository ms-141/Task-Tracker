import sqlite3

DB_PATH = "database.db"

def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    return connection

def query_one(sql, params=()):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(sql, params)
    row = cursor.fetchone()
    conn.close()
    return row


def execute(sql, params=()):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(sql, params)
    connection.commit()
    last_id = cursor.lastrowid
    connection.close()
    return last_id



# Users
def create_user(login_name, password_hash, user_email=None):
    return execute(
        """
        INSERT OR IGNORE INTO users (login_name, password_hash, user_email)
        VALUES (?, ?, ?)
        """,
        (login_name, password_hash, user_email)
    )

def get_user_by_login(login_name, password_hash, user_email=None):
    return execute(
        """
        INSERT OR IGNORE INTO users (login_name, password_hash, user_email)
        VALUES (?, ?, ?)
        """,
        (login_name, password_hash, user_email)
    )

def get_user_by_id(login_name):
    return query_one(
        "SELECT * FROM users WHERE login_name = ?",
        (login_name)   
    )

# Tasks

def create_task(user_id, title, course, due_date, difficulty, importance, remaining_minutes):
    return

def list_active_tasks(user_id):
    return

def update_task_remaining_minutes(task_id, remaining_minutes):
    return

# Daily

def upsert_daily_context(user_id, entry_date, available_minutes, energy_level=None, buffer_minutes=0):
    return

def get_daily_context(user_id, entry_date):
    return




def generate_daily_plan(user_id, entry_date):
    return


if __name__ == "__main__": 
    pass





