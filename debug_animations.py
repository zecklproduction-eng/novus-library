import sqlite3
import os

DB_PATH = os.path.join(os.getcwd(), 'library.db')

def list_animations():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    try:
        print("--- Custom Animations ---")
        c.execute("SELECT id, user_id, animation_type, name, file_path, is_active, category FROM custom_animations")
        rows = c.fetchall()
        for row in rows:
            print(f"ID: {row[0]}, User: {row[1]}, Type: {row[2]}, Name: {row[3]}, Path: {row[4]}, Active: {row[5]}, Cat: {row[6]}")

        # print("\n--- Animation Settings ---")
        # c.execute("SELECT user_id, setting_key, setting_value FROM animation_settings")
        # rows = c.fetchall()
        # for row in rows:
        #     print(f"User: {row[0]}, Key: {row[1]}, Value: {row[2]}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    list_animations()
