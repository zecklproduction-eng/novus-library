import sqlite3

conn = sqlite3.connect('library.db')
c = conn.cursor()

# Add more default channels to existing groups
c.execute("SELECT id FROM community_groups")
groups = c.fetchall()

for (group_id,) in groups:
    # Check existing channels
    c.execute("SELECT name FROM group_channels WHERE group_id = ?", (group_id,))
    existing = [row[0] for row in c.fetchall()]
    
    # Add channels if they don't exist
    new_channels = [
        ('events', 'Upcoming events and meetups', 'text', 'calendar', 2),
        ('media', 'Share images and videos', 'text', 'image', 3),
        ('off-topic', 'Casual conversations', 'text', 'coffee', 4),
        ('recommendations', 'Share and get recommendations', 'text', 'star', 5),
    ]
    
    for name, desc, ctype, icon, pos in new_channels:
        if name not in existing:
            c.execute('''
                INSERT INTO group_channels (group_id, name, description, channel_type, icon, position)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (group_id, name, desc, ctype, icon, pos))

conn.commit()
print(f"Added channels to {len(groups)} groups!")
conn.close()
