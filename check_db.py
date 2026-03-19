import sqlite3

def check_db():
    conn = sqlite3.connect('library.db')
    cursor = conn.cursor()
    
    print("--- Achievements ---")
    cursor.execute("SELECT name, slug, requirement_type, requirement_value FROM achievements")
    for row in cursor.fetchall():
        print(row)
        
    print("\n--- User Achievements for user with 1000+ charisma ---")
    # First find a user with 1000+ charisma
    cursor.execute("SELECT id, username, charisma FROM users WHERE charisma >= 1000")
    users = cursor.fetchall()
    for user_id, username, charisma in users:
        print(f"User: {username} (ID: {user_id}, Charisma: {charisma})")
        cursor.execute("""
            SELECT a.name, a.slug 
            FROM user_achievements ua 
            JOIN achievements a ON ua.achievement_id = a.id 
            WHERE ua.user_id = ?
        """, (user_id,))
        achs = cursor.fetchall()
        print(f"  Achievements: {achs}")
        
    conn.close()

if __name__ == "__main__":
    check_db()
