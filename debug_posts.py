
import sqlite3

def check_posts():
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    print("Checking posts for Group 1...")
    c.execute("SELECT id, title, post_type, channel_id FROM group_posts WHERE group_id = 1")
    posts = c.fetchall()
    
    print(f"Found {len(posts)} posts:")
    for p in posts:
        print(f"ID: {p[0]}, Type: {p[2]}, Channel: '{p[3]}', Title: {p[1]}")
        
    conn.close()

if __name__ == "__main__":
    check_posts()
