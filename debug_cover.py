import sqlite3
import os

# Check if the actual file exists
cover_path = "static/covers/Screenshot_2025-12-12_205946.png"
print(f"File exists at {cover_path}: {os.path.exists(cover_path)}")

# Simulate what the API does
conn = sqlite3.connect('library.db')
c = conn.cursor()
c.execute("SELECT id, title, author, cover_path FROM books WHERE title LIKE '%ONE%'")
for row in c.fetchall():
    cover = row[3]
    if cover and not cover.startswith('http') and not cover.startswith('/'):
        cover = f'/static/{cover}'
    elif not cover:
        cover = 'https://via.placeholder.com/200x300?text=No+Cover'
    print(f"ID: {row[0]}, Title: {row[1]}, Final Cover URL: {cover}")
    
    # Check if the actual path exists
    actual_path = cover.lstrip('/')
    print(f"  Actual path '{actual_path}' exists: {os.path.exists(actual_path)}")

conn.close()
