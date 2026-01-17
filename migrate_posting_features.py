import sqlite3

def migrate():
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    
    print("--- Running Migrations ---")
    
    # 1. Add attachment columns to group_posts (optional if we use a separate table, but one-to-one is easier for simple implementation)
    # Actually, the user wants "options like discord", implying multiple or different types. 
    # Let's go with separate tables for flexibility.
    
    # 2. group_post_attachments
    print("Creating group_post_attachments table...")
    c.execute("""
        CREATE TABLE IF NOT EXISTS group_post_attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            file_url TEXT NOT NULL,
            file_type TEXT NOT NULL,
            file_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES group_posts(id)
        )
    """)
    
    # 3. group_comments
    print("Creating group_comments table...")
    c.execute("""
        CREATE TABLE IF NOT EXISTS group_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES group_posts(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # 4. group_comment_attachments
    print("Creating group_comment_attachments table...")
    c.execute("""
        CREATE TABLE IF NOT EXISTS group_comment_attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            comment_id INTEGER NOT NULL,
            file_url TEXT NOT NULL,
            file_type TEXT NOT NULL,
            file_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (comment_id) REFERENCES group_comments(id)
        )
    """)
    
    # 5. group_comment_likes
    print("Creating group_comment_likes table...")
    c.execute("""
        CREATE TABLE IF NOT EXISTS group_comment_likes (
            user_id INTEGER NOT NULL,
            comment_id INTEGER NOT NULL,
            PRIMARY KEY (user_id, comment_id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (comment_id) REFERENCES group_comments(id)
        )
    """)

    conn.commit()
    conn.close()
    print("--- Migrations Finished ---")

if __name__ == "__main__":
    migrate()
