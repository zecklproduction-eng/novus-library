import sqlite3
import os

DB_PATH = 'library.db'

def list_pending():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, user_id, requested_role, status, created_at FROM role_requests WHERE status='pending'")
    rows = c.fetchall()
    print("ALL Pending Requests:")
    for r in rows:
        print(r)
    conn.close()

if __name__ == "__main__":
    list_pending()
