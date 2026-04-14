import sys

path = 'app.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.read()

old_sql = """            SELECT DISTINCT value as file_path, 
            CASE 
                WHEN type = 'animation_avatar' OR type = 'avatar_bg' THEN 'avatar'
                WHEN type = 'animation_login' OR type = 'login' THEN 'login'
                WHEN type = 'animation_logout' OR type = 'logout' THEN 'logout'
                WHEN type = 'animation_banner' OR type = 'banner' THEN 'banner'
                WHEN type = 'animation_manga' OR type = 'manga_enter' OR type = 'manga' THEN 'manga'
                ELSE type 
            END as type
            FROM shop_items 
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
            FROM custom_animations"""

new_sql = """            SELECT DISTINCT value as file_path, 
            CASE 
                WHEN type = 'animation_avatar' OR type = 'avatar_bg' THEN 'avatar'
                WHEN type = 'animation_login' OR type = 'login' THEN 'login'
                WHEN type = 'animation_logout' OR type = 'logout' THEN 'logout'
                WHEN type = 'animation_banner' OR type = 'banner' THEN 'banner'
                WHEN type = 'animation_manga' OR type = 'manga_enter' OR type = 'manga' THEN 'manga'
                ELSE type 
            END as type,
            COALESCE(name, '') as name
            FROM shop_items 
            UNION
            SELECT DISTINCT file_path, 
            CASE 
                WHEN animation_type = 'animation_avatar' OR animation_type = 'avatar_bg' THEN 'avatar'
                WHEN animation_type = 'animation_login' OR animation_type = 'login' THEN 'login'
                WHEN animation_type = 'animation_logout' OR animation_type = 'logout' THEN 'logout'
                WHEN animation_type = 'animation_banner' OR animation_type = 'banner' THEN 'banner'
                WHEN animation_type = 'animation_manga' OR animation_type = 'manga_enter' OR animation_type = 'manga' THEN 'manga'
                ELSE animation_type 
            END as type,
            COALESCE(name, '') as name
            FROM custom_animations"""

if old_sql in lines:
    print("Found old SQL, replacing...")
    new_content = lines.replace(old_sql, new_sql)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Done.")
else:
    print("Old SQL not found exactly. Checking for partial match or manual update needed.")
    # Fallback to a simpler replace if needed
