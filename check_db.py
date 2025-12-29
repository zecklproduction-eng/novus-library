
import sqlite3
import os

db_path = r"d:\nist project\computer\library\novus-library\library.db"
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
c = conn.cursor()

print("Columns in custom_animations:")
c.execute("PRAGMA table_info(custom_animations)")
for row in c.fetchall():
    print(row)

print("\nContent of custom_animations:")
c.execute("SELECT * FROM custom_animations")
for row in c.fetchall():
    print(row)

conn.close()
