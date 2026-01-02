
import sqlite3
import os

DB_PATH = 'd:\\nist project\\computer\\library\\novus-library\\instance\\library.db'

def check_chapters():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print("--- Chapters ---")
    c.execute("SELECT id, manga_id, chapter_num, title, page_count FROM chapters ORDER BY created_at DESC LIMIT 10")
    rows = c.fetchall()
    for row in rows:
        print(row)
        
    print("\n--- Manga ---")
    c.execute("SELECT id, title FROM books WHERE book_type='manga' OR category='Manga' LIMIT 5")
    rows = c.fetchall()
    for row in rows:
        print(row)
        
    conn.close()

if __name__ == "__main__":
    check_chapters()
