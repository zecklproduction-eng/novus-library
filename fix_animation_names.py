import sqlite3
import os

DB_PATH = os.path.join(os.getcwd(), 'library.db')

def fix_names():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    try:
        # Find 'majuk' in manga_enter
        c.execute("SELECT id, name FROM custom_animations WHERE name LIKE '%majuk%' AND animation_type = 'manga_enter'")
        rows = c.fetchall()
        for row in rows:
            print(f"Renaming ID {row[0]} ('{row[1]}') to 'Majuk Manga'")
            c.execute("UPDATE custom_animations SET name = 'Majuk Manga' WHERE id = ?", (row[0],))
        
        conn.commit()
        print("Done.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    fix_names()
