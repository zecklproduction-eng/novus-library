import sqlite3
import os

DB_PATH = r"d:\nist project\computer\library\novus-library\library.db"

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print("Starting migrations...")

    # Create event_tasks table
    c.execute("""
    CREATE TABLE IF NOT EXISTS event_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER NOT NULL,
        description TEXT NOT NULL,
        coin_reward INTEGER NOT NULL,
        task_type TEXT NOT NULL, -- 'normal', 'limited'
        FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
    )
    """)
    print("Created 'event_tasks' table.")

    # Create user_event_task_progress table
    c.execute("""
    CREATE TABLE IF NOT EXISTS user_event_task_progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        task_id INTEGER NOT NULL,
        status TEXT DEFAULT 'pending', -- 'pending', 'completed'
        completed_at TIMESTAMP,
        UNIQUE(user_id, task_id),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (task_id) REFERENCES event_tasks(id) ON DELETE CASCADE
    )
    """)
    print("Created 'user_event_task_progress' table.")

    # Check if 'prize_shop_item_id' exists in 'events'
    c.execute("PRAGMA table_info(events)")
    columns = [row[1] for row in c.fetchall()]
    if 'prize_shop_item_id' not in columns:
        try:
            conn.execute("ALTER TABLE events ADD COLUMN prize_shop_item_id INTEGER")
            print("Added 'prize_shop_item_id' column to 'events' table.")
        except Exception as e:
            print(f"Error adding prize_shop_item_id: {e}")

    conn.commit()
    conn.close()
    print("Migrations completed successfully.")

if __name__ == "__main__":
    migrate()
