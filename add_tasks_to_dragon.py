import sqlite3

db_path = 'library.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

# Get the ID of the 'dark fansity dragon' event
c.execute("SELECT id FROM events WHERE name = 'dark fansity dragon'")
row = c.fetchone()
if row:
    event_id = row[0]
    # Add some sample tasks
    tasks = [
        (event_id, "Defeat the Dark Dragon in some way", 50, "normal"),
        (event_id, "Collect 10 Dragon Scales", 40, "limited"),
        (event_id, "Explore the Fantasy Realm", 20, "normal")
    ]
    c.executemany("INSERT INTO event_tasks (event_id, description, coin_reward, task_type) VALUES (?, ?, ?, ?)", tasks)
    conn.commit()
    print(f"Added {len(tasks)} tasks to event 'dark fansity dragon' (ID: {event_id})")
else:
    print("Event 'dark fansity dragon' not found.")

conn.close()
