from app import init_db, get_conn

def seed():
    init_db()
    conn = get_conn()
    c = conn.cursor()
    
    # 1. Get first user
    c.execute("SELECT id FROM users LIMIT 1")
    user = c.fetchone()
    if not user:
        print("No users found. Please run the app or register a user first.")
        return
    user_id = user[0]
    
    # 2. Get some books
    c.execute("SELECT id, title FROM books LIMIT 3")
    books = c.fetchall()
    if not books:
        # Create a dummy book if none exist
        c.execute("INSERT INTO books (title, author, category, book_type) VALUES (?, ?, ?, ?)", 
                  ('Test Manga', 'Test Author', 'Action, Sci-Fi', 'manga'))
        conn.commit()
        c.execute("SELECT id, title FROM books LIMIT 1")
        books = c.fetchall()
    
    # 3. Add reviews
    review_content = 'This is a test review from the database. <span class="spoiler">Spoiler content here!</span> Real data feels good.'
    for book_id, title in books:
        # Check if review already exists to avoid duplicates
        c.execute("SELECT id FROM reviews WHERE user_id = ? AND book_id = ?", (user_id, book_id))
        if not c.fetchone():
            c.execute("""
                INSERT INTO reviews (user_id, book_id, rating, content, has_spoilers, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, book_id, 4.5, f"Review for {title}. {review_content}", 1, 'Completed'))
            print(f"Added review for {title}")
    
    conn.commit()
    conn.close()
    print("Seeding complete.")

if __name__ == "__main__":
    seed()
