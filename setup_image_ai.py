#!/usr/bin/env python3
"""
Setup script for image-to-summary AI feature
Creates database table and implements GPT-4 Vision integration
"""

import sqlite3
import os

DB_PATH = "library.db"

def setup_image_summary_table():
    """Create table for storing image summaries"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Check if table already exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='image_summaries'")
    if c.fetchone():
        print("✓ image_summaries table already exists")
        conn.close()
        return
    
    # Create table
    c.execute("""
        CREATE TABLE image_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER,
            chapter_id INTEGER,
            page_num INTEGER,
            image_path TEXT,
            summary TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (book_id) REFERENCES books(id),
            FOREIGN KEY (chapter_id) REFERENCES manga_chapters(id)
        )
    """)
    conn.commit()
    conn.close()
    print("✓ Created image_summaries table")

def check_tables():
    """Display all database tables"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = c.fetchall()
    
    print("\nDatabase tables:")
    for table in tables:
        print(f"  - {table[0]}")
    
    conn.close()

if __name__ == "__main__":
    setup_image_summary_table()
    check_tables()
    print("\n✓ Setup complete!")
