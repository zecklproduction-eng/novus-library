import sqlite3

DB_PATH = "library.db"

def migrate():
    print(f"Migrating {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        # Check if column exists
        c.execute("PRAGMA table_info(custom_animations)")
        columns = [row[1] for row in c.fetchall()]
        
        if "min_plan" not in columns:
            print("Adding min_plan column...")
            c.execute("ALTER TABLE custom_animations ADD COLUMN min_plan TEXT DEFAULT 'basic'")
            conn.commit()
            print("Migration successful.")
        else:
            print("Column min_plan already exists.")
            
    except Exception as e:
        print(f"Error during migration: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
