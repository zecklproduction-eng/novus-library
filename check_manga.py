import sqlite3
try:
    conn = sqlite3.connect('library.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, title FROM books WHERE book_type='manga' LIMIT 5")
    rows = cursor.fetchall()
    print("Manga found:", rows)
    
    # Also check if chapters exist
    if rows:
        manga_id = rows[0][0]
        cursor.execute("SELECT COUNT(*) FROM chapters WHERE manga_id=?", (manga_id,))
        print(f"Chapters for manga {manga_id}:", cursor.fetchone()[0])
        
except Exception as e:
    print(e)
finally:
    conn.close()
