import sqlite3
import os

DB_PATH = "library.db"

def migrate_posts():
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Get all posts that need migration
    c.execute("SELECT id, group_id, channel_id FROM group_posts WHERE channel_id IS NULL OR channel_id = 'default' OR channel_id = ''")
    posts_to_migrate = c.fetchall()
    
    print(f"Found {len(posts_to_migrate)} posts to migrate.")
    
    migrated_count = 0
    errors_count = 0
    
    for post in posts_to_migrate:
        post_id = post['id']
        group_id = post['group_id']
        
        # Find the 'general' channel for this group
        c.execute("SELECT id FROM group_channels WHERE group_id = ? AND name = 'general' LIMIT 1", (group_id,))
        channel_row = c.fetchone()
        
        if channel_row:
            target_channel_id = channel_row['id']
            try:
                c.execute("UPDATE group_posts SET channel_id = ? WHERE id = ?", (target_channel_id, post_id))
                migrated_count += 1
            except Exception as e:
                print(f"  Error migrating post {post_id}: {e}")
                errors_count += 1
        else:
            # Maybe the group doesn't have a 'general' channel yet? Get the first one available.
            c.execute("SELECT id FROM group_channels WHERE group_id = ? ORDER BY position ASC LIMIT 1", (group_id,))
            fallback_row = c.fetchone()
            if fallback_row:
                target_channel_id = fallback_row['id']
                c.execute("UPDATE group_posts SET channel_id = ? WHERE id = ?", (target_channel_id, post_id))
                migrated_count += 1
            else:
                print(f"  Warning: No channels found for group {group_id}. Cannot migrate post {post_id}.")
                errors_count += 1

    conn.commit()
    conn.close()
    print(f"\nFinished! Migrated {migrated_count} posts. Errors: {errors_count}")

if __name__ == "__main__":
    migrate_posts()
