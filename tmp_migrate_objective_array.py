import sqlite3
import os

db_files = ['library.db', 'database.db']

for db_file in db_files:
    if not os.path.exists(db_file):
        print(f"Skipping {db_file} as it does not exist.")
        continue
        
    try:
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        
        # Add columns to event_tasks
        try:
            c.execute("ALTER TABLE event_tasks ADD COLUMN keyword TEXT DEFAULT ''")
            c.execute("ALTER TABLE event_tasks ADD COLUMN genre TEXT DEFAULT 'All'")
            c.execute("ALTER TABLE event_tasks ADD COLUMN refresh_count_days INTEGER DEFAULT 2")
            print(f"[{db_file}] Successfully updated event_tasks schema.")
        except Exception as alt_e:
            print(f"[{db_file}] event_tasks alter error (might exist already): {alt_e}")
            
        # Create user_event_tasks table
        c.execute("""
            CREATE TABLE IF NOT EXISTS user_event_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                task_id INTEGER NOT NULL,
                last_completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print(f"[{db_file}] Verified user_event_tasks table.")
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error updating {db_file}: {e}")
