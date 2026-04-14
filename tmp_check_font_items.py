import sqlite3
import json

def check_font_settings():
    conn = sqlite3.connect('library.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    print("Checking Font Settings in DB...")
    c.execute("SELECT * FROM animation_settings WHERE setting_key LIKE '%font%'")
    rows = c.fetchall()
    if not rows:
        print("No font settings found in animation_settings.")
    else:
        for row in rows:
            print(f"User {row['user_id']}: {row['setting_key']} = {row['setting_value']}")
            
    print("\nChecking Shop Items (Fonts)...")
    c.execute("SELECT * FROM shop_items WHERE type='title_glow' AND value LIKE '%font%'")
    items = c.fetchall()
    for item in items:
        print(f"ID {item['id']}: {item['name']} (Value: {item['value']})")
        
    conn.close()

if __name__ == '__main__':
    check_font_settings()
