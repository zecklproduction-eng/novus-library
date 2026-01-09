import sqlite3
try:
    conn = sqlite3.connect('library.db')
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cursor.fetchall()]
    print("Users columns:", columns)
    
    cursor.execute("SELECT * FROM users LIMIT 1")
    print("User sample:", cursor.fetchone())

except Exception as e:
    print(e)
finally:
    conn.close()
