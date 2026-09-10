import sqlite3

DB_PATH = 'database/database.db'
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("DELETE FROM topic_importance")
cur.execute("DELETE FROM pyq_questions")

conn.commit()
conn.close()

print("Database reset complete.")