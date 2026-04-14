
import sqlite3
import os

DB_PATH = 'library.db'

def check_db():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print("--- custom_animations Table Dump ---")
    c.execute("SELECT id, user_id, animation_type, file_path, is_active FROM custom_animations")
    rows = c.fetchall()
    
    if not rows:
        print("No active animations found.")
    else:
        print(f"{'ID':<5} {'User':<5} {'Type':<15} {'Active':<8} {'Path'}")
        print("-" * 60)
        for row in rows:
            print(f"{row[0]:<5} {row[1]:<5} {row[2]:<15} {row[4]:<8} {row[3]}")

    conn.close()

if __name__ == "__main__":
    check_db()
