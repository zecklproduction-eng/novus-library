
import sqlite3
import os

DB_PATH = 'library.db'

def dump_users():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print("--- Users Table Dump ---")
    try:
        c.execute("SELECT id, username, email FROM users")
        rows = c.fetchall()
        print(f"{'ID':<5} {'Username':<15} {'Email'}")
        print("-" * 50)
        for row in rows:
            print(f"{row[0]:<5} {row[1]:<15} {row[2]}")
    except Exception as e:
        print(f"Error reading users: {e}")

    conn.close()

if __name__ == "__main__":
    dump_users()
