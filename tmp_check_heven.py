import sqlite3
import os

conn = sqlite3.connect('library.db')
c = conn.cursor()

print("--- Shop Items related to 'heven' ---")
c.execute("SELECT id, name, type, value, currency_type FROM shop_items WHERE name LIKE '%heven%'")
rows = c.fetchall()
for row in rows:
    print(row)
    # Check if the file exists if it's a path
    val = row[3]
    if val and not val.startswith(('#', 'http')):
        path = os.path.join('static', val)
        print(f"  Checking file: {path} -> Exist: {os.path.exists(path)}")

conn.close()
