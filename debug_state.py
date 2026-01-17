
import sqlite3

def check_all():
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    
    print("=== ALL POSTS IN GROUP 1 ===")
    c.execute("SELECT id, title, post_type, channel_id FROM group_posts WHERE group_id = 1")
    for row in c.fetchall():
        print(f"ID: {row[0]}, Type: {row[2]}, Channel: {row[3]}, Title: {row[1][:30] if row[1] else 'N/A'}")
    
    print("\n=== CHANNELS FOR GROUP 1 ===")
    c.execute("SELECT id, name FROM group_channels WHERE group_id = 1")
    for row in c.fetchall():
        print(f"Channel ID: {row[0]}, Name: {row[1]}")
    
    conn.close()

if __name__ == "__main__":
    check_all()
