import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    
    # 1. Create events table
    logger.info("Creating events table...")
    c.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            event_type TEXT NOT NULL, -- 'global', 'group'
            group_id INTEGER,
            creator_id INTEGER NOT NULL,
            status TEXT DEFAULT 'pending', -- 'pending', 'approved', 'rejected', 'active', 'completed'
            condition_type TEXT, -- 'posts_count', 'comment_count', 'members_joined', 'charisma_earned'
            condition_value INTEGER,
            prize_type TEXT, -- 'achievement', 'charisma'
            prize_id TEXT, -- achievement slug or amount
            start_date TEXT,
            end_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (group_id) REFERENCES community_groups (id),
            FOREIGN KEY (creator_id) REFERENCES users (id)
        )
    """)
    
    # 2. Update achievements table
    logger.info("Updating achievements table...")
    try:
        c.execute("ALTER TABLE achievements ADD COLUMN is_limited INTEGER DEFAULT 0")
        logger.info("Added 'is_limited' column to achievements.")
    except sqlite3.OperationalError:
        logger.info("'is_limited' column already exists in achievements.")
        
    try:
        c.execute("ALTER TABLE achievements ADD COLUMN event_id INTEGER")
        logger.info("Added 'event_id' column to achievements.")
    except sqlite3.OperationalError:
        logger.info("'event_id' column already exists in achievements.")
        
    conn.commit()
    conn.close()
    logger.info("Database migration complete.")

if __name__ == "__main__":
    migrate()
