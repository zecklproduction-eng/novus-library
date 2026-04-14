import sqlite3

conn = sqlite3.connect('library.db')
c = conn.cursor()

# Create group_post_votes table
c.execute('''
    CREATE TABLE IF NOT EXISTS group_post_votes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        vote INTEGER NOT NULL,  -- 1 for upvote, -1 for downvote
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(post_id, user_id),
        FOREIGN KEY (post_id) REFERENCES group_posts(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
''')

# Create group_channels table
c.execute('''
    CREATE TABLE IF NOT EXISTS group_channels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        channel_type TEXT DEFAULT 'text',  -- text, voice, announcement
        icon TEXT,
        position INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (group_id) REFERENCES community_groups(id)
    )
''')

conn.commit()
print("Tables created successfully!")

# Add default channels to existing groups
c.execute("SELECT id FROM community_groups")
groups = c.fetchall()

for (group_id,) in groups:
    # Check if group already has channels
    c.execute("SELECT COUNT(*) FROM group_channels WHERE group_id = ?", (group_id,))
    count = c.fetchone()[0]
    
    if count == 0:
        # Add default channels
        c.execute('''
            INSERT INTO group_channels (group_id, name, description, channel_type, icon, position)
            VALUES (?, 'general', 'General discussion', 'text', 'message-circle', 0)
        ''', (group_id,))
        c.execute('''
            INSERT INTO group_channels (group_id, name, description, channel_type, icon, position)
            VALUES (?, 'announcements', 'Important announcements', 'announcement', 'megaphone', 1)
        ''', (group_id,))

conn.commit()
print("Default channels added to groups!")
conn.close()
