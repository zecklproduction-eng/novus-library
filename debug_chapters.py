
import sqlite3
import os

DB_PATH = 'd:\\nist project\\computer\\library\\novus-library\\library.db'

def check_chapters():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print("--- Recent Chapters (All Manga) ---")
    c.execute("""
        SELECT c.id, b.title as manga_title, c.chapter_num, c.title as ch_title, c.page_count, c.pdf_filename, c.created_at 
        FROM chapters c
        JOIN books b ON c.manga_id = b.id
        ORDER BY c.id DESC LIMIT 20
    """)
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
