import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_and_award():
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    
    # 1. Define Charisma Achievements
    charisma_achievements = [
        ('Rising Star', 'rising_star', 'Earn 100 charisma', 'fa-star-of-life', 'cyan', 1, 'charisma', 'charisma', 100),
        ('Charismatic Icon', 'charismatic_icon', 'Earn 500 charisma', 'fa-gem', 'purple', 2, 'charisma', 'charisma', 500),
        ('Legendary Presence', 'legendary_presence', 'Earn 1000 charisma', 'fa-crown', 'yellow', 3, 'charisma', 'charisma', 1000),
        ('Top 3 Legend', 'top_3_charismatic', 'Become one of the top 3 charismatic members', 'fa-trophy', 'yellow', 1, 'charisma', 'top_3', 1)
    ]
    
    # 2. Seed missing achievements
    for name, slug, desc, icon, color, level, cat, req_type, req_val in charisma_achievements:
        try:
            c.execute("SELECT id FROM achievements WHERE slug = ?", (slug,))
            if c.fetchone():
                logger.info(f"Achievement {slug} already exists.")
                continue
            
            c.execute("""
                INSERT INTO achievements 
                (name, slug, description, icon, badge_color, level, category, requirement_type, requirement_value)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, slug, desc, icon, color, level, cat, req_type, req_val))
            logger.info(f"Seeded achievement: {name}")
        except Exception as e:
            logger.error(f"Error seeding {slug}: {e}")
            
    conn.commit()
    
    # 3. Retroactively award achievements
    logger.info("Retroactively awarding charisma achievements...")
    
    # Get all users with their charisma
    c.execute("SELECT id, username, charisma FROM users")
    users = c.fetchall()
    
    # Get charisma achievement IDs
    c.execute("SELECT id, slug, requirement_type, requirement_value FROM achievements WHERE category = 'charisma'")
    achs = {slug: {'id': aid, 'type': r_type, 'val': r_val} for aid, slug, r_type, r_val in c.fetchall()}
    
    for user_id, username, charisma in users:
        charisma = charisma or 0
        
        # Check Rising Star (100+)
        if charisma >= 100 and 'rising_star' in achs:
            award_if_missing(c, user_id, achs['rising_star']['id'], username, 'Rising Star')
            
        # Check Charismatic Icon (500+)
        if charisma >= 500 and 'charismatic_icon' in achs:
            award_if_missing(c, user_id, achs['charismatic_icon']['id'], username, 'Charismatic Icon')
            
        # Check Legendary Presence (1000+)
        if charisma >= 1000 and 'legendary_presence' in achs:
            award_if_missing(c, user_id, achs['legendary_presence']['id'], username, 'Legendary Presence')

    # Award Top 3 Legend to the current top 3
    if 'top_3_charismatic' in achs:
        c.execute("SELECT id, username FROM users ORDER BY charisma DESC LIMIT 3")
        top_3 = c.fetchall()
        for uid, uname in top_3:
            award_if_missing(c, uid, achs['top_3_charismatic']['id'], uname, 'Top 3 Legend')

    conn.commit()
    conn.close()
    logger.info("Migration and retroactive awarding complete.")

def award_if_missing(cursor, user_id, ach_id, username, ach_name):
    cursor.execute("SELECT 1 FROM user_achievements WHERE user_id = ? AND achievement_id = ?", (user_id, ach_id))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO user_achievements (user_id, achievement_id) VALUES (?, ?)", (user_id, ach_id))
        logger.info(f"Awarded {ach_name} to {username}")

if __name__ == "__main__":
    seed_and_award()
