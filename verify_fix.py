import sqlite3
import requests
import os

DB_PATH = 'library.db'

def verify():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    print("--- VERIFYING FIXES ---")
    
    # 1. Check for duplicate achievement names
    c.execute("SELECT name, COUNT(*) as c FROM achievements GROUP BY name HAVING c > 1")
    dups = c.fetchall()
    if dups:
        print(f"FAILED: Still have duplicate achievement names: {[d['name'] for d in dups]}")
    else:
        print("PASS: No duplicate achievement names.")
        
    # 2. Check for unique constraints on user_achievements
    try:
        # Try to insert a duplicate and see if it fails (using a temporary transaction)
        c.execute("SELECT user_id, achievement_id FROM user_achievements LIMIT 1")
        row = c.fetchone()
        if row:
            uid, aid = row['user_id'], row['achievement_id']
            try:
                conn.execute("INSERT INTO user_achievements (user_id, achievement_id) VALUES (?, ?)", (uid, aid))
                print("FAILED: UNIQUE constraint not working on user_achievements (insert succeeded)")
            except sqlite3.IntegrityError:
                print("PASS: UNIQUE constraint working on user_achievements")
    except Exception as e:
        print(f"Bypassing unique check (no data): {e}")

    # 3. Check for unique constraints on user_inventory
    try:
        c.execute("SELECT user_id, item_id FROM user_inventory LIMIT 1")
        row = c.fetchone()
        if row:
            uid, iid = row['user_id'], row['item_id']
            try:
                conn.execute("INSERT INTO user_inventory (user_id, item_id) VALUES (?, ?)", (uid, iid))
                print("FAILED: UNIQUE constraint not working on user_inventory (insert succeeded)")
            except sqlite3.IntegrityError:
                print("PASS: UNIQUE constraint working on user_inventory")
    except Exception as e:
        print(f"Bypassing unique check (no data): {e}")

    conn.close()

if __name__ == "__main__":
    verify()
