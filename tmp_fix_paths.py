import sqlite3

conn = sqlite3.connect('library.db')
c = conn.cursor()

# Remove leading /static/ from item values to ensure url_for works correctly
print("Cleaning up shop_items paths...")
c.execute("UPDATE shop_items SET value = REPLACE(value, '/static/', '') WHERE value LIKE '/static/%'")
print(f"  Modified {c.rowcount} rows in shop_items.")

# Same for custom_animations just in case
c.execute("UPDATE custom_animations SET file_path = REPLACE(file_path, '/static/', '') WHERE file_path LIKE '/static/%'")
print(f"  Modified {c.rowcount} rows in custom_animations.")

conn.commit()
conn.close()
print("Database cleanup complete.")
