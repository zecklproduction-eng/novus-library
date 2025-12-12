#!/usr/bin/env python3
"""
Debug script to check books in the database
"""

import sqlite3
import os

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_ROOT, "library.db")

def check_books():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Check table schema
    print("=" * 60)
    print("BOOKS TABLE SCHEMA:")
    print("=" * 60)
    c.execute("PRAGMA table_info(books)")
    columns = c.fetchall()
    for col in columns:
        print(f"  {col[1]}: {col[2]}")
    
    # Count books by type
    print("\n" + "=" * 60)
    print("BOOKS BY TYPE:")
    print("=" * 60)
    c.execute("SELECT COALESCE(book_type, 'book'), COUNT(*) FROM books GROUP BY COALESCE(book_type, 'book')")
    results = c.fetchall()
    for book_type, count in results:
        print(f"  {book_type}: {count}")
    
    # Show all books
    print("\n" + "=" * 60)
    print("ALL BOOKS:")
    print("=" * 60)
    c.execute("SELECT id, title, author, COALESCE(book_type, 'book') FROM books")
    books = c.fetchall()
    if books:
        for book_id, title, author, book_type in books:
            print(f"  [{book_id}] {title} by {author} (type: {book_type})")
    else:
        print("  No books found in database")
    
    conn.close()

if __name__ == "__main__":
    check_books()
