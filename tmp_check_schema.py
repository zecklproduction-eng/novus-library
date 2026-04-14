import sqlite3

def check_schema():
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    c.execute("PRAGMA table_info(shop_items);")
    columns = c.fetchall()
    for col in columns:
        print(f"Column: {col[1]}, Type: {col[2]}")
    conn.close()

if __name__ == "__main__":
    check_schema()
