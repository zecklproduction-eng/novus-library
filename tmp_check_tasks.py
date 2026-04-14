import sqlite3

try:
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("PRAGMA table_info(event_tasks)")
    print("event_tasks:", c.fetchall())
    c.execute("PRAGMA table_info(user_event_tasks)")
    print("user_event_tasks:", c.fetchall())
    conn.close()
except Exception as e:
    print(f"Error checking database.db: {e}")

try:
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    c.execute("PRAGMA table_info(event_tasks)")
    print("event_tasks (library.db):", c.fetchall())
    c.execute("PRAGMA table_info(user_event_tasks)")
    print("user_event_tasks (library.db):", c.fetchall())
    conn.close()
except Exception as e:
    print(f"Error checking library.db: {e}")
