import sqlite3
conn = sqlite3.connect('library.db')
c = conn.cursor()

print("=== ALL USER_INVENTORY entries ===")
for row in c.execute("""
    SELECT ui.id, ui.user_id, ui.item_id, s.name, s.type, s.value, s.currency_type 
    FROM user_inventory ui 
    JOIN shop_items s ON ui.item_id = s.id 
    ORDER BY ui.user_id, s.type
"""):
    print(row)

print("\n=== SHOP_ITEMS with animation in type ===")
for row in c.execute("SELECT * FROM shop_items WHERE type LIKE '%anim%'"):
    print(row)

print("\n=== CUSTOM_ANIMATIONS for user_id=1 ===")
for row in c.execute("SELECT id, animation_type, file_path, is_active, name, category FROM custom_animations WHERE user_id = 1"):
    print(row)

conn.close()
