import sqlite3
try:
    conn = sqlite3.connect('library.db')
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(custom_animations)")
    columns = [row[1] for row in cursor.fetchall()]
    print("custom_animations columns:", columns)

except Exception as e:
    print(e)
finally:
    conn.close()
