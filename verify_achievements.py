import sqlite3
import json

def verify_achievements():
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    c.execute("""
        SELECT name, category, level, requirement_type, requirement_value 
        FROM achievements 
        WHERE slug IN (
            'manga_rookie_1', 'manga_explorer_5', 'manga_enthusiast_10', 
            'otaku_50_ch', 'master_otaku_200_ch', 'voice_novus_1', 
            'active_talker_10', 'insightful_peer_5', 'community_regular_25', 
            'curator_10_fav'
        )
        ORDER BY category, level
    """)
    rows = c.fetchall()
    print(json.dumps(rows, indent=2))
    conn.close()

if __name__ == "__main__":
    verify_achievements()
