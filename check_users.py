import sqlite3
conn = sqlite3.connect('library.db')
c = conn.cursor()
c.execute("SELECT id, username, role FROM users")
for row in c.fetchall():
    print(row)
conn.close()
