import sqlite3

conn = sqlite3.connect('library.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

print("--- Shop Items Samples ---")
c.execute("SELECT value, type FROM shop_items LIMIT 20")
for row in c.fetchall():
    print(f"Value: {row['value']}, Type: {row['type']}")

print("\n--- Custom Animations Samples ---")
c.execute("SELECT file_path, animation_type FROM custom_animations LIMIT 20")
for row in c.fetchall():
    print(f"Path: {row['file_path']}, Type: {row['animation_type']}")

conn.close()
