
import sqlite3

def fix_and_verify():
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    
    # Fix all posts with NULL channel_id - assign to channel 1 (general) for group 1
    c.execute("""
        UPDATE group_posts 
        SET channel_id = (
            SELECT id FROM group_channels 
            WHERE group_id = group_posts.group_id AND name = 'general' 
            LIMIT 1
        )
        WHERE channel_id IS NULL
    """)
    fixed_count = c.rowcount
    conn.commit()
    
    print(f"Fixed {fixed_count} posts with NULL channel_id")
    
    # Verify
    c.execute("SELECT id, post_type, channel_id FROM group_posts WHERE group_id = 1")
    print("\n=== POSTS AFTER FIX ===")
    for row in c.fetchall():
        print(f"ID: {row[0]}, Type: {row[1]}, Channel: {row[2]}")
    
    conn.close()

if __name__ == "__main__":
    fix_and_verify()
