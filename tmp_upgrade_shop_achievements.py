import sqlite3

for db_file in ['database.db', 'library.db']:
    try:
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        c.execute("""
            UPDATE achievements 
            SET level = 5, rarity = 'legend', animation_type = 'pulsing' 
            WHERE slug LIKE 'shop_purchased_%'
        """)
        print(f"Updated {c.rowcount} shop achievements in {db_file}")
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error updating {db_file}: {e}")
