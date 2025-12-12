#!/usr/bin/env python3
"""
Migration script to add book_type column to existing books table.
Run this if manga books aren't showing up after updating the code.
"""

import sqlite3
import os

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_ROOT, "library.db")

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        # Try to add book_type column
        c.execute("ALTER TABLE books ADD COLUMN book_type TEXT DEFAULT 'book'")
        conn.commit()
        print("✓ Successfully added book_type column to books table")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e):
            print("✓ book_type column already exists")
        else:
            print(f"✗ Error: {e}")
            return
    
    # Verify the column exists
    c.execute("PRAGMA table_info(books)")
    columns = [col[1] for col in c.fetchall()]
    
    if "book_type" in columns:
        print("✓ Verified: book_type column exists")
        print("\nYour database is ready!")
        print("You can now upload manga and they will appear on the manga page.")
    else:
        print("✗ Failed to add book_type column")
    
    conn.close()

if __name__ == "__main__":
    print("Starting database migration...")
    migrate()
