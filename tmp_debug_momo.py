import sqlite3
import os

db_path = r'd:\nist project\computer\library\novus-library\library.db'
if not os.path.exists(db_path):
    print(f"DB not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute("SELECT name, value, type FROM shop_items WHERE name LIKE '%momo%' OR value LIKE '%momo%';")
rows = c.fetchall()
if not rows:
    print("No momo items found in shop_items")
else:
    for row in rows:
        print(f"Name: {row[0]}, Value: {row[1]}, Type: {row[2]}")

# Also check for other tables
c.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = c.fetchall()
print(f"Tables: {tables}")
conn.close()
