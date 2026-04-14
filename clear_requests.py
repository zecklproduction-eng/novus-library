import sqlite3
import os

DB_PATH = 'library.db'

def clear_pending(user_id=3):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM role_requests WHERE user_id=? AND status='pending'", (user_id,))
    print(f"Deleted {c.rowcount} pending requests for user {user_id}")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    clear_pending()
