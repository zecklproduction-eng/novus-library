import sqlite3
import os

DB_PATH = 'library.db'

def cleanup():
    if not os.path.exists(DB_PATH):
        print(f"Error: {DB_PATH} not found.")
        return
        
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    print("--- STARTING ACHIEVEMENTS CLEANUP ---")
    
    # 1. Clean up potential duplicates in user_achievements BEFORE creating index
    # Find combinations that appear MORE than once
    c.execute("SELECT user_id, achievement_id, COUNT(*) as count FROM user_achievements GROUP BY user_id, achievement_id HAVING count > 1")
    user_dups = c.fetchall()
    for ud in user_dups:
        uid, aid = ud['user_id'], ud['achievement_id']
        print(f"  Fixing user duplicate achievement: UID={uid}, AID={aid}")
        # Keep the latest, delete others
        c.execute("SELECT id FROM user_achievements WHERE user_id = ? AND achievement_id = ? ORDER BY earned_at DESC", (uid, aid))
        ids = [r[0] for r in c.fetchall()]
        to_keep = ids[0]
        to_del = ids[1:]
        for did in to_del:
            c.execute("DELETE FROM user_achievements WHERE id = ?", (did,))

    # 2. Find and merge duplicate achievement entries in 'achievements' table
    c.execute("SELECT name, COUNT(*) as count FROM achievements GROUP BY name HAVING count > 1")
    duplicates = c.fetchall()
    
    for dup in duplicates:
        name = dup['name']
        print(f"Merging achievement definition duplicates for: '{name}'")
        
        c.execute("SELECT id, slug FROM achievements WHERE name = ? ORDER BY id ASC", (name,))
        rows = c.fetchall()
        
        # Keep the first one, merge others into it
        keep_id = rows[0]['id']
        to_remove = rows[1:]
        
        for rem in to_remove:
            rem_id = rem['id']
            print(f"  Merging duplicate ID {rem_id} (slug: {rem['slug']}) into ID {keep_id}")
            
            # Map user records from 'rem' to 'keep'
            c.execute("SELECT user_id, earned_at FROM user_achievements WHERE achievement_id = ?", (rem_id,))
            user_recs = c.fetchall()
            for rec in user_recs:
                try:
                    # Try to insert into the 'keep' record
                    c.execute("INSERT INTO user_achievements (user_id, achievement_id, earned_at) VALUES (?, ?, ?)", 
                             (rec['user_id'], keep_id, rec['earned_at']))
                except sqlite3.IntegrityError:
                    # User already had the 'keep' version, so just skip
                    pass
            
            # Delete redundant user records for the 'removed' ID
            c.execute("DELETE FROM user_achievements WHERE achievement_id = ?", (rem_id,))
            
            # Update shop_items to point to the kept achievement
            c.execute("UPDATE shop_items SET achievement_id = ? WHERE achievement_id = ?", (keep_id, rem_id))
            
            # Delete the redundant achievement definition
            c.execute("DELETE FROM achievements WHERE id = ?", (rem_id,))
            
    # 3. Apply UNIQUE indices
    try:
        c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_user_ach_unique ON user_achievements(user_id, achievement_id)")
        print("Ensured UNIQUE index on user_achievements")
    except Exception as e:
        print(f"Warning: Could not create unique index on user_achievements: {e}")

    try:
        c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_user_inv_unique ON user_inventory(user_id, item_id)")
        print("Ensured UNIQUE index on user_inventory")
    except Exception as e:
        print(f"Warning: Could not create unique index on user_inventory: {e}")

    conn.commit()
    conn.close()
    print("--- CLEANUP COMPLETE ---")

if __name__ == "__main__":
    cleanup()
