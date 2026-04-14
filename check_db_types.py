import sqlite3

conn = sqlite3.connect('library.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

print("--- Shop Items ---")
c.execute("SELECT DISTINCT type FROM shop_items")
for row in c.fetchall():
    print(f"Type: {row['type']}")

print("\n--- Custom Animations ---")
c.execute("SELECT DISTINCT animation_type FROM custom_animations")
for row in c.fetchall():
    print(f"Type: {row['animation_type']}")

conn.close()
