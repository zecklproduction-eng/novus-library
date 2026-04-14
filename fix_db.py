
import sqlite3
import os

DB_PATH = "novus.db"

def fix_db():
    print(f"Connecting to {DB_PATH}...")
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
    print("Done.")

if __name__ == "__main__":
    fix_db()
