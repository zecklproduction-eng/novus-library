import sqlite3
import os

db_path = 'library.db'
if not os.path.exists(db_path):
    print(f"Database {db_path} not found.")
    exit(1)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
c = conn.cursor()

print("--- Events ---")
c.execute("SELECT id, name, status, event_type FROM events")
events = c.fetchall()
for ev in events:
    print(dict(ev))

print("\n--- Event Tasks ---")
c.execute("SELECT * FROM event_tasks")
tasks = c.fetchall()
for task in tasks:
    print(dict(task))

conn.close()
