import sqlite3
try:
    conn = sqlite3.connect('library.db')
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(reading_history)")
    columns = [row[1] for row in cursor.fetchall()]
    print("reading_history columns:", columns)

except Exception as e:
    print(e)
finally:
    conn.close()
