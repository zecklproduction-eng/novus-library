import os

def update_app_py():
    path = 'app.py'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Define the new logic for shop() and charisma_hall()
    new_admin_logic = """    is_admin = session.get("role") == "admin"
    all_achievements = []
    existing_assets = []
    if is_admin:
        c.execute("SELECT id, name, rarity, icon, badge_color FROM achievements ORDER BY name ASC")
        all_achievements = [dict(row) for row in c.fetchall()]
        
        # Fetch existing assets from both shop_items and custom_animations
        c.execute(\"\"\"
            SELECT DISTINCT value as file_path, type FROM shop_items 
            WHERE value LIKE '/static/%'
            UNION
            SELECT DISTINCT file_path, animation_type as type FROM custom_animations
            WHERE file_path LIKE '/static/%'
        \"\"\")
        existing_assets = [dict(row) for row in c.fetchall()]"""

    old_admin_logic = """    is_admin = session.get("role") == "admin"
    all_achievements = []
    if is_admin:
        c.execute("SELECT id, name FROM achievements ORDER BY name ASC")
        all_achievements = [dict(row) for row in c.fetchall()]"""

    if old_admin_logic in content:
        print("Updating shop logic...")
        content = content.replace(old_admin_logic, new_admin_logic)
    else:
        print("Could not find old admin logic block. Checking for slightly modified versions...")
        # Fallback to a simpler replace if whitespace differs
        # (This is just a safety check)

    # Return statement for shop() was already partially updated by a previous tool call?
    # No, let's make sure it's correct.
    old_return_shop = 'return render_template("shop.html", items=items, owned_ids=owned_ids, user_coins=user_coins, all_achievements=all_achievements)'
    new_return_shop = 'return render_template("shop.html", items=items, owned_ids=owned_ids, user_coins=user_coins, all_achievements=all_achievements, existing_assets=existing_assets)'
    
    if old_return_shop in content:
        content = content.replace(old_return_shop, new_return_shop)

    # Update charisma_hall return as well
    old_return_charisma = """    return render_template("charisma_hall.html", 
                           items=items, 
                           owned_ids=owned_ids, 
                           user_charisma=user_charisma,
                           all_achievements=all_achievements)"""
    new_return_charisma = """    return render_template("charisma_hall.html", 
                           items=items, 
                           owned_ids=owned_ids, 
                           user_charisma=user_charisma,
                           all_achievements=all_achievements,
                           existing_assets=existing_assets)"""
    
    if old_return_charisma in content:
        content = content.replace(old_return_charisma, new_return_charisma)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("app.py updated successfully.")

if __name__ == "__main__":
    update_app_py()
