import sqlite3
import os

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_ROOT, 'library.db')

def check():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT id, name, group_type FROM community_groups WHERE name = 'World';")
    world = c.fetchone()
    print("World Group:", world)
    
    if world:
        group_id = world[0]
        c.execute("SELECT id, name FROM group_channels WHERE group_id = ?;", (group_id,))
        channels = c.fetchall()
        print(f"Channels for {world[1]} (ID {group_id}):", channels)
        
        c.execute("SELECT count(*) FROM group_members WHERE group_id = ?;", (group_id,))
        print(f"Member count for {world[1]}:", c.fetchone()[0])
        
        # Check for any posts in this group
        c.execute("SELECT id, title FROM group_posts WHERE group_id = ? LIMIT 5;", (group_id,))
        print(f"Recent posts in {world[1]}:", c.fetchall())

    conn.close()

if __name__ == "__main__":
    check()
