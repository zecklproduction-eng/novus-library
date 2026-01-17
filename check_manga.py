import sqlite3

conn = sqlite3.connect('library.db')
c = conn.cursor()

# Check ONE PIECE cover path
c.execute("SELECT id, title, cover_path FROM books WHERE title LIKE '%ONE%' OR title LIKE '%PIECE%'")
for row in c.fetchall():
    print(f"ID: {row[0]}, Title: {row[1]}, Cover: {row[2]}")

conn.close()
