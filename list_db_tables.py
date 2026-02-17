import sqlite3
import json

def list_tables():
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in c.fetchall()]
    print(json.dumps(tables, indent=2))
    conn.close()

if __name__ == "__main__":
    list_tables()
