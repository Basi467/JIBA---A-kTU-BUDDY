import sqlite3

from db import get_db_path

DB_PATH = get_db_path()

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

a = cur.execute('select * from subjects where id = 39') 
print(a.fetchall())
    