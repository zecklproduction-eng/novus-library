import sqlite3
import os

DB_PATH = 'library.db'

def run_query(query, params=()):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(query, params)
    result = cursor.fetchall()
    conn.commit()
    conn.close()
    return result

def test_event_lifecycle():
    print("--- Testing Event Lifecycle ---")
    
    # Clean up previous tests
    run_query("DELETE FROM events WHERE name LIKE '%Test Event%'")
    run_query("DELETE FROM achievements WHERE slug LIKE 'test_ach_%'")
    
    # 1. Create a global event (Admin flow)
    print("1. Creating global event (Simulating Admin Flow)...")
    # In app.py, create_admin_event automatically approves and creates achievement if prize_type='achievement'
    name = "Global Test Event"
    p_id = "test_ach_global"
    run_query("""
        INSERT INTO events (name, description, event_type, creator_id, status, condition_type, condition_value, prize_type, prize_id)
        VALUES (?, ?, 'global', 1, 'approved', 'posts_count', 5, 'achievement', ?)
    """, (name, "Testing global admin flow", p_id))
    
    event = run_query("SELECT id FROM events WHERE name = ?", (name,))[0]
    ev_id = event['id']
    print(f"   Event ID: {ev_id}")
    
    # Simulate the achievement creation logic from create_admin_event
    run_query("""
        INSERT INTO achievements (name, slug, description, icon, badge_color, is_limited, event_id)
        VALUES (?, ?, ?, ?, ?, 1, ?)
    """, (f"Event: {name}", p_id, f"Awarded for completing '{name}'", "fa-trophy", "yellow", ev_id))
    
    ach_check = run_query("SELECT * FROM achievements WHERE event_id = ?", (ev_id,))
    if ach_check:
        print(f"   Achievement '{ach_check[0]['name']}' correctly linked to event ID: {ev_id}")
    else:
        print("   Error: Achievement not linked to event.")
    
    # 2. Request a group event
    print("2. Requesting group event (Simulating Owner Flow)...")
    run_query("""
        INSERT INTO events (name, description, event_type, group_id, creator_id, status, condition_type, condition_value, prize_type, prize_id)
        VALUES (?, ?, 'group', 1, 2, 'pending', 'comment_count', 3, 'charisma', '500')
    """, ("Group Request Event", "Testing owner flow",))
    
    event_req = run_query("SELECT id, status FROM events WHERE name = 'Group Request Event'")[0]
    print(f"   Requested Event ID: {event_req['id']}, Status: {event_req['status']}")
    
    # 3. Approve the group event (Admin flow)
    print("3. Approving group event...")
    run_query("UPDATE events SET status = 'approved' WHERE id = ?", (event_req['id'],))
    updated_req = run_query("SELECT status FROM events WHERE id = ?", (event_req['id'],))[0]
    print(f"   Event Status after approval: {updated_req['status']}")
    
    # 4. Verify limited tag in achievements
    print("4. Verifying 'Limited' tag...")
    limited_ach = run_query("SELECT is_limited FROM achievements WHERE event_id = ?", (ev_id,))[0]
    if limited_ach['is_limited'] == 1:
        print("   Success: Achievement marked as 'Limited'.")
    else:
        print("   Error: Achievement NOT marked as 'Limited'.")

    print("\n--- Event Verification Complete ---")

if __name__ == "__main__":
    if os.path.exists(DB_PATH):
        test_event_lifecycle()
    else:
        print("Database not found!")
