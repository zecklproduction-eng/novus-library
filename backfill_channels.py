import sqlite3
import os

# Database path - using absolute path to be sure
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_ROOT, "library.db")

def backfill():
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Get all groups
    c.execute("SELECT id, name FROM community_groups")
    groups = c.fetchall()
    
    # Default channels setup (Sync with app.py)
    default_channels = [
        ('general', 'General discussion for the group', 'text', 'message-circle', 1),
        ('announcements', 'Official updates and news from the group', 'text', 'megaphone', 2),
        ('events', 'Upcoming events, meetups and milestones', 'text', 'calendar', 3),
        ('media', 'Share and view images, videos and galleries', 'text', 'image', 4),
        ('off-topic', 'Casual conversations and random discussions', 'text', 'coffee', 5),
        ('recommendations', 'Share and discover new stories and series', 'text', 'star', 6),
    ]

    print(f"Starting backfill for {len(groups)} groups...")
    
    updated_groups_count = 0
    total_channels_added = 0
    
    for group_id, group_name in groups:
        # Check existing channels for this group
        c.execute("SELECT name FROM group_channels WHERE group_id = ?", (group_id,))
        existing_names = [row[0] for row in c.fetchall()]
        
        added_for_group = 0
        for name, desc, ctype, icon, pos in default_channels:
            if name not in existing_names:
                try:
                    c.execute("""
                        INSERT INTO group_channels (group_id, name, description, channel_type, icon, position)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (group_id, name, desc, ctype, icon, pos))
                    added_for_group += 1
                except Exception as e:
                    print(f"  Error adding channel {name} to group {group_name}: {e}")
        
        if added_for_group > 0:
            print(f"Group '{group_name}' (ID: {group_id}): Added {added_for_group} channels.")
            updated_groups_count += 1
            total_channels_added += added_for_group

    conn.commit()
    conn.close()
    print(f"\nFinished! Updated {updated_groups_count} groups with {total_channels_added} new channels.")

if __name__ == "__main__":
    backfill()
