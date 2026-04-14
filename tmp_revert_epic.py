import sqlite3

for db_file in ['database.db', 'library.db']:
    try:
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        c.execute("""
            UPDATE achievements 
            SET rarity = 'epic' 
            WHERE slug LIKE 'shop_purchased_%'
        """)
        print(f"Updated {c.rowcount} shop achievements back to 'epic' in {db_file}")
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error updating {db_file}: {e}")
