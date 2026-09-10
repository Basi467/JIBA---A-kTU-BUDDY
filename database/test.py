import sqlite3

DB_PATH = 'database/ktu.db'

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

a = cur.execute('select * from subjects where id = 39') 
print(a.fetchall())
    