import sqlite3

try:
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    c.execute("SELECT id, name, icon, icon_type FROM achievements WHERE slug LIKE 'shop_purchased_%'")
    for row in c.fetchall():
        print(row)
    conn.close()
except Exception as e:
    print(f"Error: {e}")
