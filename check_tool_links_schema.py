
import sqlite3
import os

DB_PATH = 'library.db'

def check_schema():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("PRAGMA table_info(tool_links)")
    columns = c.fetchall()
    for col in columns:
        print(col)
    conn.close()

if __name__ == "__main__":
    check_schema()
