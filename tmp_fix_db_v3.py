import sqlite3
import html

def repair_db():
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    
    c.execute("SELECT user_id, setting_key, setting_value FROM animation_settings WHERE setting_key LIKE 'avatar_%%'")
    rows = c.fetchall()
    
    fixed_count = 0
    for user_id, key, val in rows:
        if val and ('&#34;' in val or '&quot;' in val):
            # Unescape HTML entities
            new_val = html.unescape(val)
            c.execute("UPDATE animation_settings SET setting_value = ? WHERE user_id = ? AND setting_key = ?", (new_val, user_id, key))
            fixed_count += 1
            print(f"Repaired {key} for User {user_id}")
            
    conn.commit()
    conn.close()
    print(f"Done. Repaired {fixed_count} entries.")

if __name__ == '__main__':
    repair_db()
