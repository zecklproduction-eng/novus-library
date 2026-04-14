import sqlite3

db_path = 'library.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("SELECT id, name, status, event_type FROM events")
events = c.fetchall()
print(f"Total events found: {len(events)}")
for ev in events:
    print(ev)

c.execute("SELECT * FROM event_tasks")
tasks = c.fetchall()
print(f"Total tasks found: {len(tasks)}")
for task in tasks:
    print(task)

conn.close()
