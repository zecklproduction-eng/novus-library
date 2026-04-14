
import sqlite3
import os

DB_PATH = 'library.db'

def force_activate():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    user_id = 1  # TARGETING ADMIN USER
    preset_path = 'img/banner_option_novus_blue.png'
    
    # 1. Deactivate all banners for clean slate
    c.execute("UPDATE custom_animations SET is_active = 0 WHERE user_id = ? AND animation_type = 'banner'", (user_id,))
    
    # 2. Check if row exists
    c.execute("SELECT id FROM custom_animations WHERE user_id = ? AND file_path = ?", (user_id, preset_path))
    row = c.fetchone()
    
    if row:
        print(f"Found existing row ID {row[0]}. Activating...")
        c.execute("UPDATE custom_animations SET is_active = 1 WHERE id = ?", (row[0],))
    else:
        print("No row found. Inserting new record...")
        c.execute("INSERT INTO custom_animations (user_id, animation_type, file_path, is_active) VALUES (?, 'banner', ?, 1)", 
                  (user_id, preset_path))
    
    conn.commit()
    print("Force activation complete for User 1.")
    
    # Verify
    c.execute("SELECT is_active, file_path FROM custom_animations WHERE user_id = ? AND is_active = 1 AND animation_type='banner'", (user_id,))
    row = c.fetchone()
    if row:
        print(f"VERIFIED: Active Banner Path = {row[1]}")
    else:
        print("VERIFICATION FAILED: No active banner found.")
        
    conn.close()

if __name__ == "__main__":
    force_activate()
