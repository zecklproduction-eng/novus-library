import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "library.db")
print("Using DB:", DB_PATH)

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

try:
    c.execute("ALTER TABLE users ADD COLUMN status TEXT DEFAULT 'active'")
    print("Column 'status' added.")
except sqlite3.OperationalError as e:
    # This will happen if the column already exists – that's OK.
    print("Got sqlite error:", e)

# Show table schema so we can double-check:
c.execute("PRAGMA table_info(users)")
print("users columns:")
for row in c.fetchall():
    print(row)

conn.commit()
conn.close()
print("Done.")
