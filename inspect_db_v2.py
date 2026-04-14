import sqlite3

conn = sqlite3.connect('library.db')
c = conn.cursor()

print("--- Tables ---")
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in c.fetchall()]
for table in tables:
    print(f"\n- {table}")
    c.execute(f"PRAGMA table_info({table})")
    cols = c.fetchall()
    for col in cols:
        print(f"  {col[1]} ({col[2]})")

conn.close()
