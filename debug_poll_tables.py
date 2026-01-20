import sqlite3
import os

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_ROOT, 'library.db')

def check():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("PRAGMA table_info(group_polls);")
    columns = [r[1] for r in c.fetchall()]
    print("Columns in group_polls:", columns)
    
    c.execute("PRAGMA table_info(group_poll_options);")
    columns = [r[1] for r in c.fetchall()]
    print("Columns in group_poll_options:", columns)

    conn.close()

if __name__ == "__main__":
    check()
