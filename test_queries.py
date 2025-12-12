#!/usr/bin/env python3
"""
Test script to verify manga query works correctly
"""

import sqlite3
import os

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_ROOT, "library.db")

def test_manga_query():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Run the exact query from the manga route
    base_sql = """
        SELECT id, title, author, COALESCE(category,'General') AS category,
               pdf_filename, audio_filename, cover_path
        FROM books
        WHERE COALESCE(book_type,'book')='manga'
    """
    base_sql += " ORDER BY datetime(created_at) DESC"
    
    print("Running manga query:")
    print(base_sql)
    print("\n" + "=" * 60)
    
    c.execute(base_sql)
    mangas = c.fetchall()
    
    print(f"Found {len(mangas)} manga(s):\n")
    for manga in mangas:
        manga_id, title, author, category, pdf, audio, cover = manga
        print(f"  ID: {manga_id}")
        print(f"  Title: {title}")
        print(f"  Author: {author}")
        print(f"  Category: {category}")
        print(f"  Cover: {cover}")
        print()
    
    # Also show what the home page query returns (should NOT include manga)
    print("=" * 60)
    print("Verifying home page query (should exclude manga):")
    print("=" * 60)
    
    home_sql = """
        SELECT id, title, author, COALESCE(category,'General') AS category,
               pdf_filename, audio_filename, cover_path
        FROM books
        WHERE COALESCE(book_type, 'book') != 'manga'
    """
    home_sql += " ORDER BY datetime(created_at) DESC"
    
    c.execute(home_sql)
    books = c.fetchall()
    print(f"Found {len(books)} regular book(s):\n")
    for book in books:
        book_id, title, author, category, pdf, audio, cover = book
        print(f"  ID: {book_id}")
        print(f"  Title: {title}")
        print(f"  Author: {author}")
        print(f"  Category: {category}")
        print()
    
    conn.close()

if __name__ == "__main__":
    test_manga_query()
