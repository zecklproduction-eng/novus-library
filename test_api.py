import sqlite3

# Simulate the exact API logic
conn = sqlite3.connect('library.db')
c = conn.cursor()

query = "one"  # Test search for "one"
search_term = query.replace('-', ' ')

c.execute("""
    SELECT id, title, author, cover_path 
    FROM books 
    WHERE (book_type = 'manga' OR category LIKE '%Manga%')
    AND title LIKE ? 
    LIMIT 10
""", (f"%{search_term}%",))

rows = c.fetchall()
print(f"Found {len(rows)} results for query '{query}':")

for row in rows:
    cover = row[3]
    # Ensure cover path is a proper URL
    if cover and not cover.startswith('http') and not cover.startswith('/'):
        cover = f'/static/{cover}'
    elif not cover:
        cover = 'https://via.placeholder.com/200x300?text=No+Cover'
    
    print(f"  ID: {row[0]}")
    print(f"  Title: {row[1]}")
    print(f"  Author: {row[2]}")
    print(f"  Cover (raw): {row[3]}")
    print(f"  Cover (final): {cover}")
    print()

conn.close()
