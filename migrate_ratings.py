import sqlite3
import os

def migrate():
    db_path = 'library.db'
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found.")
        return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    try:
        # 1. Create manga_comment_likes table
        print("Creating manga_comment_likes table...")
        c.execute("""
            CREATE TABLE IF NOT EXISTS manga_comment_likes (
                user_id INTEGER NOT NULL,
                comment_id INTEGER NOT NULL,
                PRIMARY KEY (user_id, comment_id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (comment_id) REFERENCES manga_comments(id)
            )
        """)

        # 2. Create manga_chapter_ratings table
        print("Creating manga_chapter_ratings table...")
        c.execute("""
            CREATE TABLE IF NOT EXISTS manga_chapter_ratings (
                user_id INTEGER NOT NULL,
                chapter_id INTEGER NOT NULL,
                rating INTEGER NOT NULL, -- 1 for like, -1 for dislike
                PRIMARY KEY (user_id, chapter_id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (chapter_id) REFERENCES chapters(id)
            )
        """)

        conn.commit()
        print("Migration successful.")
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
