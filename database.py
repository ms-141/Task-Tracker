import sqlite3
# import datetime



connection = sqlite3.connect("database.db")
cursor = connection.cursor()

cursor.execute("PRAGMA foreign_keys = ON;")

cursor.executescript("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_email TEXT NOT NULL UNIQUE,
    login_name TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
               
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    course TEXT,
    due_date TEXT NOT NULL,
    difficulty INTEGER NOT NULL,
    importance INTEGER NOT NULL,
    remaining_minutes INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
               
CREATE TABLE IF NOT EXISTS daily_context (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    entry_date TEXT NOT NULL, 
    available_minutes INTEGER NOT NULL,
    energy_level INTEGER,
    buffer_minutes INTEGER DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (user_id, entry_date),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
""")
# x = datetime.datetime.now()
# test = [
#     ('test_user'+ str(x.second), 'hashed_password', x)
# ]
# cursor.execute("INSERT INTO users (login_name, password_hash, created_at) VALUES (?, ?, ?);", test[0])

# for row in cursor.execute("SELECT * FROM users"):
#     print(row)

connection.commit()
connection.close()