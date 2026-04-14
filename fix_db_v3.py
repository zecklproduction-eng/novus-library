
import sqlite3
import os

# Use dynamic path matching app.py logic
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(APP_ROOT, "library.db")

def fix_db():
    target_db_path = DEFAULT_DB_PATH
    print(f"Connecting to {target_db_path}...")
    
    if not os.path.exists(target_db_path):
        print("WARNING: DB file not found at expected path!")
        if os.path.exists("library.db"):
            print("Found library.db in current directory, using that.")
            target_db_path = "library.db"
    
    conn = sqlite3.connect(target_db_path)
    c = conn.cursor()
    
    print(f"Creating transactions table in {target_db_path}...")
    c.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id TEXT PRIMARY KEY,
            user_id INTEGER,
            amount REAL,
            currency TEXT DEFAULT 'USD',
            status TEXT, -- completed, refunded, pending
            type TEXT, -- subscription, one-time, ads, bundle
            item TEXT, -- Pro Plan, Bundle Name, etc.
            invoice_id TEXT,
            created_at TEXT DEFAULT (DATETIME('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    conn.commit()
    conn.close()
    print("Done. Transactions table created successfully.")

if __name__ == "__main__":
    fix_db()
