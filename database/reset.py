import sqlite3

from db import get_db_path

DB_PATH = get_db_path()
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("DELETE FROM topic_importance")
cur.execute("DELETE FROM pyq_questions")

conn.commit()
conn.close()

print("Database reset complete.")