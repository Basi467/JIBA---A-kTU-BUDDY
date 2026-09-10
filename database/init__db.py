import sqlite3

DB_PATH = 'database/ktu.db'

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

with open('database/schema.sql', 'r') as f:
    cur.executescript(f.read())

conn.commit()
conn.close()

print("Database initialized successfully.")