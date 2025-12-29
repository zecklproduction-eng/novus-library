import sqlite3
import os

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_ROOT, "library.db")

def migrate():
    print(f"Connecting to {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        print("Adding 'category' column to 'custom_animations' table...")
        c.execute("ALTER TABLE custom_animations ADD COLUMN category TEXT DEFAULT 'animation'")
        conn.commit()
        print("Column added successfully.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("Column 'category' already exists.")
        else:
            print(f"Error: {e}")
    
    conn.close()

if __name__ == "__main__":
    migrate()
