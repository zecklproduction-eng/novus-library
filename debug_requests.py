import sqlite3
import os

DB_PATH = 'library.db'

def check_requests():
    if not os.path.exists(DB_PATH):
        print("DB not found")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, user_id, requested_role, status, created_at FROM role_requests ORDER BY created_at DESC LIMIT 5")
    rows = c.fetchall()
    print("Latest 5 Request Entries:")
    for r in rows:
        print(r)
    conn.close()

if __name__ == "__main__":
    check_requests()
