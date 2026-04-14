import sqlite3
import os

DB_PATH = "library.db"

def verify():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT group_id, COUNT(*) FROM group_channels GROUP BY group_id")
    counts = c.fetchall()
    
    c.execute("SELECT id, name FROM community_groups")
    groups = {row[0]: row[1] for row in c.fetchall()}
    
    print(f"{'Group ID':<10} | {'Channels':<10} | {'Group Name'}")
    print("-" * 50)
    
    fully_updated = True
    for gid, count in counts:
        print(f"{gid:<10} | {count:<10} | {groups.get(gid, 'Unknown')}")
        if count < 6:
            fully_updated = False
            
    # Check if any groups have 0 channels (not in group_channels yet)
    groups_with_channels = [gid for gid, count in counts]
    for gid, name in groups.items():
        if gid not in groups_with_channels:
            print(f"{gid:<10} | 0          | {name}")
            fully_updated = False
            
    if fully_updated:
        print("\nAll groups have at least 6 channels!")
    else:
        print("\nSome groups are still missing channels.")
        
    conn.close()

if __name__ == "__main__":
    verify()
