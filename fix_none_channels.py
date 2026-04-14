
import sqlite3
import os

DB_PATH = 'library.db'

def fix_none_channels():
    if not os.path.exists(DB_PATH):
        print(f"Error: {DB_PATH} not found.")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        print("Fixing posts with channel_id NULL or 'None'...")
        
        # Update NULL or 'None' string to 1 (General for Group 1)
        cursor.execute("UPDATE group_posts SET channel_id = 1 WHERE channel_id IS NULL OR channel_id = 'None'")
        
        rows = cursor.rowcount
        conn.commit()
        
        print(f"Fixed {rows} posts. They now have channel_id=1 (General).")
        
        # Verify
        cursor.execute("SELECT id, channel_id FROM group_posts WHERE group_id = 1")
        posts = cursor.fetchall()
        print("Current posts in Group 1:")
        for p in posts:
            print(f"ID: {p[0]}, Channel: {p[1]}")
            
        conn.close()
    except Exception as e:
        print(f"Fix failed: {e}")

if __name__ == "__main__":
    fix_none_channels()
