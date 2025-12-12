#!/usr/bin/env python3
"""
Test script to insert a manga and verify it shows up
"""

import sqlite3
import os
from datetime import datetime

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_ROOT, "library.db")

def add_test_manga():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Insert a test manga
    test_manga = {
        "title": "Test Manga - Sword Art Online",
        "author": "Reki Kawahara",
        "category": "Action",
        "pdf_filename": None,
        "audio_filename": None,
        "cover_path": None,
        "uploader_id": 2,  # publisher user
        "book_type": "manga",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    c.execute("""
        INSERT INTO books 
        (title, author, category, pdf_filename, audio_filename, cover_path, uploader_id, book_type, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        test_manga["title"],
        test_manga["author"],
        test_manga["category"],
        test_manga["pdf_filename"],
        test_manga["audio_filename"],
        test_manga["cover_path"],
        test_manga["uploader_id"],
        test_manga["book_type"],
        test_manga["created_at"]
    ))
    
    conn.commit()
    print(f"✓ Inserted test manga: {test_manga['title']}")
    
    # Verify it can be queried
    c.execute("""
        SELECT id, title, book_type FROM books 
        WHERE book_type = 'manga'
    """)
    mangas = c.fetchall()
    print(f"\n✓ Manga books in database: {len(mangas)}")
    for manga_id, title, book_type in mangas:
        print(f"  [{manga_id}] {title} (type: {book_type})")
    
    conn.close()

if __name__ == "__main__":
    add_test_manga()
