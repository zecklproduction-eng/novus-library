import sqlite3
conn = sqlite3.connect('novus.db')
c = conn.cursor()
c.execute("PRAGMA table_info(custom_animations)")
for row in c.fetchall():
    print(row)
conn.close()
