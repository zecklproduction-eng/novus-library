import sqlite3

conn = sqlite3.connect("library.db")
c = conn.cursor()

# check existing columns
c.execute("PRAGMA table_info(users)")
cols = {row[1] for row in c.fetchall()}

if "status" not in cols:
    c.execute("ALTER TABLE users ADD COLUMN status TEXT DEFAULT 'active'")

if "pending_publisher" not in cols:
    c.execute("ALTER TABLE users ADD COLUMN pending_publisher INTEGER DEFAULT 0")

conn.commit()
conn.close()
print("✅ users table updated (status, pending_publisher)")
