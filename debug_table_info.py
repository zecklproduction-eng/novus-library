import sqlite3
import os

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_ROOT, 'library.db')

def check():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("PRAGMA table_info(group_post_attachments);")
    columns = [r[1] for r in c.fetchall()]
    print("Columns in group_post_attachments:", columns)
    
    c.execute("PRAGMA table_info(group_channels);")
    columns = [r[1] for r in c.fetchall()]
    print("Columns in group_channels:", columns)

    conn.close()

if __name__ == "__main__":
    check()
