import sqlite3

for db_file in ['database.db', 'library.db']:
    try:
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        c.execute("""
            UPDATE achievements 
            SET icon_type = 'image' 
            WHERE slug LIKE 'shop_purchased_%' AND (icon LIKE '/%' OR icon LIKE '%.png' OR icon LIKE '%.jpg' OR icon LIKE '%.gif')
        """)
        print(f"Updated {c.rowcount} shop achievements to 'image' icon_type in {db_file}")
        
        c.execute("""
            UPDATE achievements 
            SET icon_type = 'fontawesome' 
            WHERE slug LIKE 'shop_purchased_%' AND icon NOT LIKE '/%' AND icon NOT LIKE '%.png' AND icon NOT LIKE '%.jpg' AND icon NOT LIKE '%.gif'
        """)
        print(f"Updated {c.rowcount} shop achievements to 'fontawesome' icon_type in {db_file}")
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error updating {db_file}: {e}")
