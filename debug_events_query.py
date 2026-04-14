import sqlite3
from datetime import datetime

conn = sqlite3.connect('library.db')
c = conn.cursor()
c.row_factory = sqlite3.Row

d_str = datetime.now().strftime('%Y-%m-%d')
print(f"Current Date: {d_str}")

c.execute("SELECT id, name, status, end_date FROM events")
all_rows = [dict(r) for r in c.fetchall()]
print(f"All events in DB: {all_rows}")

c.execute("""
    SELECT e.id, e.name, e.end_date
    FROM events e
    WHERE e.status IN ('approved', 'active') 
      AND (e.end_date IS NULL OR e.end_date = '' OR e.end_date >= ?)
""", (d_str,))
filtered_rows = [dict(r) for r in c.fetchall()]
print(f"Filtered events: {filtered_rows}")

conn.close()
