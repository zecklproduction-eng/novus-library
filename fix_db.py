import sqlite3
import os

DB_PATH = "library.db"

def fix_database():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    try:
        # Check if column exists
        c.execute("PRAGMA table_info(custom_animations)")
        columns = [info[1] for info in c.fetchall()]
        
        if 'has_animated' not in columns:
            print("Adding 'has_animated' column to custom_animations table...")
            c.execute("ALTER TABLE custom_animations ADD COLUMN has_animated INTEGER DEFAULT 0")
            print("Column added successfully.")
        else:
            print("'has_animated' column already exists.")
            
        # Optional: Migration from has_embedded_text if needed
        if 'has_embedded_text' in columns:
            print("Migrating data from 'has_embedded_text' to 'has_animated'...")
            c.execute("UPDATE custom_animations SET has_animated = has_embedded_text WHERE has_embedded_text IS NOT NULL")
            # SQLite doesn't support DROP COLUMN easily in older versions, so we'll leave it for now
            # or we could do a table recreation, but that's risky for a quick fix.
            print("Data migrated.")
            
        conn.commit()
        print("Database fix completed successfully.")
        
    except sqlite3.OperationalError as e:
        print(f"OperationalError: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    fix_database()
