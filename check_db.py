import sqlite3
import os

db_path = r"d:\nist project\computer\library\novus-library\library.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT id, animation_type, file_path, name, is_active FROM custom_animations WHERE name LIKE '%Jungle%' OR name LIKE '%Moonlit%';")
    rows = c.fetchall()
    for row in rows:
        print(row)
    conn.close()
else:
    print("Database not found")
