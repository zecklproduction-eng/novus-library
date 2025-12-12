import sqlite3
import os

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_ROOT, "library.db")

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Create publisher if missing
c.execute("""
    INSERT OR IGNORE INTO users (username, password, role)
    VALUES (?, ?, ?)
""", ("publisher", "123", "publisher"))

conn.commit()

print("Current users:")
for row in c.execute("SELECT id, username, role FROM users"):
    print(row)

conn.close()
print("Done.")
