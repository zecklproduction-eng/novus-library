import sqlite3

# Connect to database (creates it if missing)
connection = sqlite3.connect('library.db')
cursor = connection.cursor()

print("1. Creating Books table (With PDF & Audio support)...")
cursor.execute('''
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        author TEXT,
        category TEXT,
        pdf_filename TEXT,
        audio_filename TEXT
    )
''')

print("2. Creating Users table (With Roles)...")
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
''')

print("3. Creating History table (For Smart Profile)...")
cursor.execute('''
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        book_id INTEGER,
        date_read DATE
    )
''')

print("4. Adding Admin & Student accounts...")
try:
    # Admin User
    cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                   ('admin', '123', 'admin'))
    # Student User
    cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                   ('student', '123', 'student'))
except sqlite3.IntegrityError:
    print("   (Users already exist, skipping...)")

print("5. Adding a Dummy Book...")
cursor.execute('''
    INSERT INTO books (title, author, category, pdf_filename, audio_filename)
    VALUES ('The Great Gatsby', 'F. Scott Fitzgerald', 'Fiction', 'gatsby.pdf', 'gatsby.mp3')
''')

connection.commit()
connection.close()

print("✅ Success! Database created correctly with 'role' column.")