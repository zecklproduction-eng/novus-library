import sqlite3

def test_query():
    conn = sqlite3.connect('library.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    query = """
        SELECT DISTINCT value as file_path, 
        CASE 
            WHEN type = 'animation_avatar' OR type = 'avatar_bg' THEN 'avatar'
            WHEN type = 'animation_login' OR type = 'login' THEN 'login'
            WHEN type = 'animation_logout' OR type = 'logout' THEN 'logout'
            WHEN type = 'animation_banner' OR type = 'banner' THEN 'banner'
            WHEN type = 'animation_manga' OR type = 'manga_enter' OR type = 'manga' THEN 'manga'
            ELSE type 
        END as type
        FROM shop_items 
        WHERE value LIKE '/static/%'
        UNION
        SELECT DISTINCT file_path, 
        CASE 
            WHEN animation_type = 'animation_avatar' OR animation_type = 'avatar_bg' THEN 'avatar'
            WHEN animation_type = 'animation_login' OR animation_type = 'login' THEN 'login'
            WHEN animation_type = 'animation_logout' OR animation_type = 'logout' THEN 'logout'
            WHEN animation_type = 'animation_banner' OR animation_type = 'banner' THEN 'banner'
            WHEN animation_type = 'animation_manga' OR animation_type = 'manga_enter' OR animation_type = 'manga' THEN 'manga'
            ELSE animation_type 
        END as type
        FROM custom_animations
        WHERE file_path LIKE '/static/%'
    """
    
    c.execute(query)
    rows = [dict(row) for row in c.fetchall()]
    print(f"Total assets found: {len(rows)}")
    for r in rows[:10]:
        print(f"File: {r['file_path']}, Type: {r['type']}")
    
    conn.close()

if __name__ == "__main__":
    test_query()
