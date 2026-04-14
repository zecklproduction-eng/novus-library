
import sqlite3
import os

# Use dynamic path matching app.py logic
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_ROOT, "library.db")

def fix_db():
    print(f"Connecting to {DB_PATH}...")
    if not os.path.exists(DB_PATH):
        print("WARNING: DB file not found at expected path!")
        # Fallback to current dir if not found (though APP_ROOT should be correct)
        if os.path.exists("library.db"):
            print("Found library.db in current directory, using that.")
            DB_PATH = "library.db"
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print("Creating transactions table if not exists...")
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
    print("Done. Transactions table created.")

if __name__ == "__main__":
    fix_db()
