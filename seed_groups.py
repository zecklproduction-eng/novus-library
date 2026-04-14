import sqlite3
import os

db_path = r'd:\nist project\computer\library\novus-library\library.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get existing genres from books
cursor.execute("SELECT category FROM books WHERE category IS NOT NULL AND category != '';")
all_categories = cursor.fetchall()
unique_genres = set()
for (cat_str,) in all_categories:
    for g in cat_str.split(','):
        unique_genres.add(g.strip())

# Add some standard ones just in case
standard_genres = ['Action', 'Adventure', 'Comedy', 'Drama', 'Fantasy', 'Horror', 'Mystery', 'Romance', 'Sci-Fi', 'Slice of Life', 'Sports', 'Thriller', 'Historical', 'Psychological', 'Supernatural', 'Seinen', 'Shoujo', 'Shounen', 'Isekai']
for sg in standard_genres:
    unique_genres.add(sg)

# Get existing group names
cursor.execute("SELECT name FROM community_groups WHERE group_type = 'genre';")
existing_groups = {row[0] for row in cursor.fetchall()}

# Descriptions for common genres
descriptions = {
    'Shounen': 'Manga and anime aimed at young male audiences, typically featuring action and adventure.',
    'Shoujo': 'Manga and anime aimed at young female audiences, often focusing on romance and interpersonal relationships.',
    'Seinen': 'Manga and anime aimed at adult men, usually featuring more mature themes and complex stories.',
    'Isekai': 'Stories where a character is transported to or reborn in another world.',
    'Drama': 'Stories focusing on emotional and relational development between characters.',
    'Thriller': 'Suspenseful stories with high stakes and intense pacing.',
    'Historical': 'Stories set in a specific historical period.',
    'Psychological': 'Stories exploring the mental and emotional states of characters.',
    'Supernatural': 'Stories featuring elements that cannot be explained by science, like ghosts or magic.'
}

# Seed missing groups
new_groups_count = 0
for genre in unique_genres:
    if genre and genre not in existing_groups:
        desc = descriptions.get(genre, f"A community for fans of {genre} stories!")
        cursor.execute("""
            INSERT INTO community_groups (name, description, group_type, category, is_auto_created)
            VALUES (?, ?, 'genre', 'Manga', 1)
        """, (genre, desc))
        new_groups_count += 1

conn.commit()
print(f"Added {new_groups_count} new genre groups.")

# Also add groups for popular manga (if they don't exist)
cursor.execute("SELECT id, title FROM books WHERE book_type = 'manga' LIMIT 10;")
mangas = cursor.fetchall()

cursor.execute("SELECT name FROM community_groups WHERE group_type = 'manga';")
existing_manga_groups = {row[0] for row in cursor.fetchall()}

manga_groups_added = 0
for manga_id, title in mangas:
    if title not in existing_manga_groups:
        cursor.execute("""
            INSERT INTO community_groups (name, description, group_type, reference_id, is_auto_created)
            VALUES (?, ?, 'manga', ?, 1)
        """, (title, f"Discussion group for {title}", manga_id))
        manga_groups_added += 1

conn.commit()
print(f"Added {manga_groups_added} new manga groups.")

conn.close()
