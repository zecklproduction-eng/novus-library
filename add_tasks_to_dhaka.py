import sqlite3

db_path = 'library.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

# Get the ID of the 'dhaka' event
c.execute("SELECT id FROM events WHERE name = 'dhaka'")
row = c.fetchone()
if row:
    event_id = row[0]
    # Add some sample tasks
    tasks = [
        (event_id, "Read 5 chapters of any manga", 20, "normal"),
        (event_id, "Post 3 reviews in the community", 30, "limited"),
        (event_id, "Earn 100 charisma", 50, "normal")
    ]
    c.executemany("INSERT INTO event_tasks (event_id, description, coin_reward, task_type) VALUES (?, ?, ?, ?)", tasks)
    conn.commit()
    print(f"Added {len(tasks)} tasks to event 'dhaka' (ID: {event_id})")
else:
    print("Event 'dhaka' not found.")

conn.close()
