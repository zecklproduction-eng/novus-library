import sqlite3
import json
import sys

try:
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("PRAGMA table_info(achievements);")
    cols = dict([(row[1], type(row).__name__) for row in c.fetchall()])
    print(cols)
except Exception as e:
    print(f"Error checking database.db: {e}")

try:
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    c.execute("PRAGMA table_info(achievements);")
    cols = [row[1] for row in c.fetchall()]
    print("library.db:", cols)
except Exception as e:
    print(f"Error checking library.db: {e}")
