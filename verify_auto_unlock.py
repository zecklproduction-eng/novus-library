from app import sync_achievements
import sqlite3

def verify_auto_unlock():
    user_id = 1 # admin
    print(f"Syncing achievements for user {user_id}...")
    sync_achievements(user_id)
    
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    
    # Check if 'test_auto_unlock' is awarded
    c.execute("""
        SELECT a.name 
        FROM user_achievements ua 
        JOIN achievements a ON ua.achievement_id = a.id 
        WHERE ua.user_id = ? AND a.slug = 'test_auto_unlock'
    """, (user_id,))
    res = c.fetchone()
    if res:
        print(f"SUCCESS: Achievement '{res[0]}' was automatically unlocked!")
    else:
        print("FAILURE: Achievement was not unlocked.")
        
    conn.close()

if __name__ == "__main__":
    verify_auto_unlock()
