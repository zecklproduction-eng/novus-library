import sqlite3

conn = sqlite3.connect('library.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

print("--- shop_items Columns ---")
c.execute("PRAGMA table_info(shop_items)")
for row in c.fetchall():
    print(dict(row))

print("\n--- custom_animations Columns ---")
c.execute("PRAGMA table_info(custom_animations)")
for row in c.fetchall():
    print(dict(row))

print("\n--- Users Table (for profile display) ---")
c.execute("PRAGMA table_info(users)")
for row in c.fetchall():
    print(dict(row))

conn.close()
