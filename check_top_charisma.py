import sqlite3

def check_top_charisma():
    conn = sqlite3.connect('library.db')
    cursor = conn.cursor()
    
    print("--- Top 10 Charismatic Members ---")
    cursor.execute("SELECT id, username, charisma FROM users ORDER BY charisma DESC LIMIT 10")
    top_members = cursor.fetchall()
    for i, (uid, username, charisma) in enumerate(top_members):
        print(f"{i+1}. {username} (ID: {uid}, Charisma: {charisma})")
        
        # Check if they have the 'top_3_charismatic' achievement
        cursor.execute("""
            SELECT 1 FROM user_achievements ua 
            JOIN achievements a ON ua.achievement_id = a.id 
            WHERE ua.user_id = ? AND a.slug = 'top_3_charismatic'
        """, (uid,))
        has_ach = cursor.fetchone() is not None
        print(f"   Has 'Top 3 Legend': {has_ach}")
        
    conn.close()

if __name__ == "__main__":
    check_top_charisma()
