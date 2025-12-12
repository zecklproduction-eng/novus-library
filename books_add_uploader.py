import sqlite3

conn = sqlite3.connect("library.db")
c = conn.cursor()

try:
    c.execute("ALTER TABLE books ADD COLUMN uploader_id INTEGER")
    print("Added uploader_id column.")
except sqlite3.OperationalError:
    print("uploader_id already exists; skipping.")

conn.commit()
conn.close()
print("Done.")
