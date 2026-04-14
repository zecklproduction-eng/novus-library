import sqlite3
import os

def migrate():
    db_paths = ['library.db', 'database.db']
    for db in db_paths:
        if not os.path.exists(db):
            print(f"Skipping {db} (not found)")
            continue
            
        print(f"Migrating {db}...")
        conn = sqlite3.connect(db)
        c = conn.cursor()
        
        try:
            # Check if column exists
            c.execute("PRAGMA table_info(shop_items)")
            cols = [col[1] for col in c.fetchall()]
            if 'rarity' not in cols:
                c.execute("ALTER TABLE shop_items ADD COLUMN rarity TEXT DEFAULT 'common'")
                print(f"Added 'rarity' column to {db}")
            else:
                print(f"'rarity' column already exists in {db}")
            
            conn.commit()
        except Exception as e:
            print(f"Error migrating {db}: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    migrate()
