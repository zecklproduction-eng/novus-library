from flask import (
    Flask, render_template, request, redirect,
    session, url_for, flash
)
import sqlite3
from datetime import datetime
from collections import Counter
import os
from werkzeug.utils import secure_filename
from functools import wraps

# -------------------- PATHS / CONFIG --------------------
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_ROOT, "library.db")

UPLOAD_FOLDER_PDF    = os.path.join(APP_ROOT, "static", "books")
UPLOAD_FOLDER_AUDIO  = os.path.join(APP_ROOT, "static", "audio")
UPLOAD_FOLDER_COVERS = os.path.join(APP_ROOT, "static", "covers")

os.makedirs(UPLOAD_FOLDER_PDF, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_AUDIO, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_COVERS, exist_ok=True)

ALLOWED_PDF   = {"pdf"}
ALLOWED_AUDIO = {"mp3"}

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "novus_secret_key")


# -------------------- HELPERS --------------------
def get_conn():
    """Return a connection to the SQLite DB."""
    return sqlite3.connect(DB_PATH)

@app.before_request
def check_banned():
    uid = session.get("user_id")
    if not uid:
        return
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT status FROM users WHERE id=?", (uid,))
    row = c.fetchone()
    conn.close()
    if row and row[0] == "banned":
        session.clear()
        flash("Your account has been banned.", "danger")
        return redirect(url_for("login"))


def allowed(filename, allowed_set):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_set


def admin_required(f):
    """Allow only admin to access the route."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Admin access required.", "danger")
            return redirect(url_for("home"))
        return f(*args, **kwargs)
    return wrapper


def role_required(*roles):
    """Allow only the given roles to access the route."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if session.get("role") not in roles:
                flash("You do not have permission to access this page.", "danger")
                return redirect(url_for("home"))
            return f(*args, **kwargs)
        return wrapper
    return decorator


# -------------------- DB INIT --------------------
def init_db():
    conn = get_conn()
    c = conn.cursor()

    # users
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            email    TEXT UNIQUE,
            password TEXT,
            role     TEXT
        )
    """)

    # books (with uploader_id and book_type)
    c.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id             INTEGER PRIMARY KEY,
            title          TEXT,
            author         TEXT,
            category       TEXT,
            pdf_filename   TEXT,
            audio_filename TEXT,
            created_at     TEXT,
            cover_path     TEXT,
            uploader_id    INTEGER,
            book_type      TEXT DEFAULT 'book'
        )
    """)

    # Run quick user-table migrations for older DBs: ensure email, is_banned, status columns exist
    try:
        c.execute("ALTER TABLE users ADD COLUMN email TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE users ADD COLUMN is_banned INTEGER DEFAULT 0")
        conn.commit()
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE users ADD COLUMN status TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    # Add book_type column if it doesn't exist (migration for existing DBs)
    try:
        c.execute("ALTER TABLE books ADD COLUMN book_type TEXT DEFAULT 'book'")
        conn.commit()
    except sqlite3.OperationalError:
        # Column already exists, that's fine
        pass

    # created_at trigger
    c.execute("""
        CREATE TRIGGER IF NOT EXISTS books_created_at_default
        AFTER INSERT ON books
        WHEN NEW.created_at IS NULL
        BEGIN
            UPDATE books
            SET created_at = DATETIME('now')
            WHERE id = NEW.id;
        END;
    """)

    # reading history
    c.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id        INTEGER PRIMARY KEY,
            user_id   INTEGER,
            book_id   INTEGER,
            date_read DATE
        )
    """)

    # watchlist
    c.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            id         INTEGER PRIMARY KEY,
            user_id    INTEGER NOT NULL,
            book_id    INTEGER NOT NULL,
            status     TEXT DEFAULT 'planned',
            progress   INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (DATETIME('now')),
            UNIQUE(user_id, book_id)
        )
    """)

    # team
    c.execute("""
        CREATE TABLE IF NOT EXISTS team (
            id          INTEGER PRIMARY KEY,
            full_name   TEXT NOT NULL,
            role        TEXT,
            bio         TEXT,
            avatar_path TEXT,
            initials    TEXT,
            created_at  TEXT
        )
    """)
        # role change / publisher requests
    c.execute("""
    CREATE TABLE IF NOT EXISTS role_requests (
      id INTEGER PRIMARY KEY,
      user_id INTEGER NOT NULL,
      requested_role TEXT NOT NULL,           -- e.g. 'publisher'
      status TEXT NOT NULL DEFAULT 'pending', -- pending / approved / rejected
      created_at TEXT DEFAULT (DATETIME('now'))
    )
    """)

    # manga chapters
    c.execute("""
        CREATE TABLE IF NOT EXISTS chapters (
            id          INTEGER PRIMARY KEY,
            manga_id    INTEGER NOT NULL,
            chapter_num INTEGER NOT NULL,
            title       TEXT,
            pdf_filename TEXT,
            created_at  TEXT DEFAULT (DATETIME('now')),
            FOREIGN KEY (manga_id) REFERENCES books(id),
            UNIQUE(manga_id, chapter_num)
        )
    """)


    # default users
    try:
        c.execute("INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)",
                  ("admin", "admin@novus.local", "123", "admin"))
        c.execute("INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)",
                  ("publisher", "publisher@novus.local", "123", "publisher"))
        c.execute("INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)",
                  ("student", "student@novus.local", "123", "student"))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()



# -------------------- ROUTES --------------------
# ---------- Home / Dashboard ----------
@app.route("/")
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))

    selected = (request.args.get("category") or "").strip()
    query = (request.args.get("q") or "").strip()

    conn = get_conn()
    c = conn.cursor()

    # Categories
    c.execute("SELECT DISTINCT COALESCE(category,'General') FROM books ORDER BY 1")
    db_categories = [row[0] for row in c.fetchall()]

    extra_categories = [
        "Action", "Adventure", "Children", "Comedy", "Drama", "Fantasy",
        "General", "Historical", "Horror", "Mystery", "Poetry",
        "Romance", "Science Fiction", "Supernatural", "Thriller", "Young Adult",
    ]
    categories = sorted(set(db_categories + extra_categories + ["General"]))

    # ✅ Actual books query (this is what your cards need) - EXCLUDE MANGA
    base_sql = """
        SELECT id,
               title,
               author,
               COALESCE(category,'General') AS category,
               pdf_filename,
               audio_filename,
               cover_path
        FROM books
        WHERE COALESCE(book_type, 'book') != 'manga'
    """
    params = []

    if selected:
        base_sql += " AND COALESCE(category,'General') = ?"
        params.append(selected)

    if query:
        # simple search across title and author
        base_sql += " AND (title LIKE ? OR author LIKE ?)"
        likeq = f"%{query}%"
        params.extend([likeq, likeq])

    base_sql += " ORDER BY datetime(created_at) DESC"

    c.execute(base_sql, params)
    books = c.fetchall()

    conn.close()

    return render_template(
        "index.html",
        books=books,
        user_role=session.get("role"),
        categories=categories,
        selected_category=selected,
        search_query=query,
        page_endpoint="home",
    )

# ---------- Auth ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        conn = get_conn()
        c = conn.cursor()
        c.execute("""
    SELECT id, username, password, role, COALESCE(is_banned,0)
    FROM users
    WHERE username=? AND password=?
""", (username, password))

        user = c.fetchone()
        conn.close()

        if not user:
            return render_template("login.html", error="Invalid username or password.")

        # status index = 4
        if user[4] == "banned":
            return render_template(
                "login.html",
                error="Your account has been banned. Please contact the administrator."
                  )


        session["user_id"] = user[0]
        session["username"] = user[1]
        session["role"] = user[3]
        return redirect(url_for("home"))

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    # If user is already logged in, send them home
    if session.get("user_id"):
        return redirect(url_for("home"))

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        email = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""
        confirm  = request.form.get("confirm_password") or ""
        account_type = (request.form.get("account_type") or "reader").strip().lower()

        # Basic validation
        if not username or not email or not password:
            flash("Username, email, and password are required.", "danger")
            return redirect(url_for("register"))

        if "@" not in email or "." not in email:
            flash("Please enter a valid email address.", "danger")
            return redirect(url_for("register"))

        if len(password) < 3:
            flash("Password must be at least 3 characters.", "danger")
            return redirect(url_for("register"))

        if password != confirm:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("register"))

        # Determine role based on account_type
        # use 'reader' as the standard non-publisher role (was 'student' previously)
        if account_type == "publisher":
            role = "publisher"
        else:
            role = "reader"

        # Insert into DB
        conn = get_conn()
        c = conn.cursor()
        try:
            c.execute(
                "INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)",
                (username, email, password, role)
            )
            conn.commit()
        except sqlite3.IntegrityError as e:
            # Check which field caused the duplicate
            conn.close()
            if "username" in str(e):
                flash("That username is already taken. Choose another.", "danger")
            elif "email" in str(e):
                flash("That email is already registered. Use another or login.", "danger")
            else:
                flash("Registration failed. Please try again.", "danger")
            return redirect(url_for("register"))

        # Get the user id we just created
        c.execute("SELECT id, role FROM users WHERE username=?", (username,))
        row = c.fetchone()
        conn.close()

        # Log the user in
        session["user_id"] = row[0]
        session["username"] = username
        session["role"] = row[1]

        if role == "publisher":
            # Immediately assign publisher role so owner can access upload if desired
            flash("Publisher account created. You can now upload content.", "success")
        else:
            flash("Account created. Welcome to NOVUS!", "success")
        return redirect(url_for("home"))

    # GET request → show form
    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------- Book Detail ----------
@app.route("/book/<int:id>")
def view_book(id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_conn()
    c = conn.cursor()

    # fetch book
    c.execute(
        "SELECT id, title, author, category, pdf_filename, audio_filename, cover_path  FROM books WHERE id=?",
        (id,),
    )
    book = c.fetchone()
    if not book:
        conn.close()
        flash("Book not found.", "danger")
        return redirect(url_for("home"))

    user_id = session["user_id"]

    # record in history once per user/book
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute("SELECT 1 FROM history WHERE user_id=? AND book_id=?", (user_id, id))
    if not c.fetchone():
        c.execute(
            "INSERT INTO history (user_id, book_id, date_read) VALUES (?, ?, ?)",
            (user_id, id, today),
        )
        conn.commit()

    # watchlist entry for this user/book (if any)
    c.execute(
        "SELECT status, progress FROM watchlist WHERE user_id=? AND book_id=?",
        (user_id, id),
    )
    watchlist_row = c.fetchone()
    current_status = watchlist_row[0] if watchlist_row else None

    # --- recommendations (other books) ---
    try:
        c.execute("""
            SELECT id, title, author, category, cover_path
            FROM books
            WHERE id != ?
            ORDER BY RANDOM()
            LIMIT 3
        """, (id,))
        recommendations = c.fetchall()
    except sqlite3.OperationalError:
        c.execute("""
            SELECT id, title, author, category
            FROM books
            WHERE id != ?
            ORDER BY RANDOM()
            LIMIT 3
        """, (id,))
        recommendations = c.fetchall()

    # --- top wishlisted ---
    try:
        c.execute("""
            SELECT b.id, b.title, b.category, b.cover_path, COUNT(*) as cnt
            FROM watchlist w
            JOIN books b ON b.id = w.book_id
            GROUP BY b.id, b.title, b.category, b.cover_path
            ORDER BY cnt DESC
            LIMIT 3
        """)
        top_wishlisted = c.fetchall()
    except sqlite3.OperationalError:
        c.execute("""
            SELECT b.id, b.title, b.category, COUNT(*) as cnt
            FROM watchlist w
            JOIN books b ON b.id = w.book_id
            GROUP BY b.id, b.title, b.category
            ORDER BY cnt DESC
            LIMIT 3
        """)
        top_wishlisted = c.fetchall()

    # fetch reviews
    c.execute("""
        SELECT r.id, r.content, r.rating, r.created_at,
               u.username, u.id
        FROM reviews r
        JOIN users u ON u.id = r.user_id
        WHERE r.book_id=?
        ORDER BY datetime(r.created_at) DESC
    """, (id,))
    reviews = c.fetchall()

    conn.close()

    # map DB status -> pretty label
    status_labels = {
        "watching": "Watching",
        "on_hold": "On-Hold",
        "planned": "Plan to Watch",
        "dropped": "Dropped",
        "completed": "Completed",
    }

    return render_template(
    "book_detail.html",
    book=book,
    reviews=reviews,
    recommendations=recommendations,
    top_wishlisted=top_wishlisted
)



@app.post("/book/<int:id>/review")
def add_review(id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    content = (request.form.get("content") or "").strip()
    rating_raw = request.form.get("rating")

    try:
        rating = int(rating_raw) if rating_raw else None
    except ValueError:
        rating = None

    if not content and rating is None:
        flash("Please write a comment or give a rating.", "warning")
        return redirect(url_for("view_book", id=id))

    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO reviews (user_id, book_id, rating, content) VALUES (?, ?, ?, ?)",
        (user_id, id, rating, content),
    )
    conn.commit()
    conn.close()

    flash("Review added.", "success")
    return redirect(url_for("view_book", id=id))

@app.post("/review/<int:review_id>/delete")
def delete_review(review_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    role = session.get("role")

    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT user_id, book_id FROM reviews WHERE id=?", (review_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        flash("Review not found.", "danger")
        return redirect(url_for("home"))

    owner_id, book_id = row

    # owner or admin can delete
    if owner_id != user_id and role != "admin":
        conn.close()
        flash("You cannot delete this review.", "danger")
        return redirect(url_for("view_book", id=book_id))

    c.execute("DELETE FROM reviews WHERE id=?", (review_id,))
    conn.commit()
    conn.close()
    flash("Review deleted.", "success")
    return redirect(url_for("view_book", id=book_id))


# ---------- Add Book (Admin + Publisher) ----------
@app.route("/add", methods=["GET", "POST"])
@role_required("admin", "publisher")
def add_book():
    if request.method == "GET":
        return render_template("add_book.html")

    title    = (request.form.get("title") or "").strip()
    author   = (request.form.get("author") or "").strip()
    category = (request.form.get("category") or "").strip()
    book_type = (request.form.get("book_type") or "book").lower().strip()

    if not title:
        flash("Title is required.", "danger")
        return redirect(url_for("add_book"))

    if book_type not in ("book", "manga"):
        book_type = "book"

    pdf_filename   = None
    audio_filename = None
    cover_path     = None
    uploader_id    = session.get("user_id")

    # Handle BOOK type upload
    if book_type == "book":
        # PDF: support pdf_file or book_file
        pdf_file = request.files.get("pdf_file") or request.files.get("book_file")
        if pdf_file and pdf_file.filename:
            ext = pdf_file.filename.rsplit(".", 1)[-1].lower()
            if ext in ALLOWED_PDF:
                pdf_filename = secure_filename(pdf_file.filename)
                pdf_file.save(os.path.join(UPLOAD_FOLDER_PDF, pdf_filename))
            else:
                flash("Digital book must be a .pdf file.", "danger")

        # Audio
        audio_file = request.files.get("audio_file")
        if audio_file and audio_file.filename:
            ext = audio_file.filename.rsplit(".", 1)[-1].lower()
            if ext in ALLOWED_AUDIO:
                audio_filename = secure_filename(audio_file.filename)
                audio_file.save(os.path.join(UPLOAD_FOLDER_AUDIO, audio_filename))
            else:
                flash("Audiobook must be a .mp3 file.", "danger")

        # Cover
        cover_file = request.files.get("cover_image")
        if cover_file and cover_file.filename:
            fname = secure_filename(cover_file.filename)
            cover_file.save(os.path.join(UPLOAD_FOLDER_COVERS, fname))
            cover_path = f"covers/{fname}"

        conn = get_conn()
        c = conn.cursor()
        c.execute("""
        INSERT INTO books (title, author, category, pdf_filename, audio_filename, cover_path, book_type)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (title, author, category, pdf_filename, audio_filename, cover_path, book_type))
        conn.commit()
        conn.close()

        flash("Book published successfully.", "success")
        return redirect(url_for("home"))

    # Handle MANGA type upload
    elif book_type == "manga":
        description = (request.form.get("description") or "").strip()
        status = (request.form.get("status") or "ongoing").lower().strip()

        if status not in ("ongoing", "completed", "hiatus"):
            status = "ongoing"

        # Cover image (required for manga)
        cover_file = request.files.get("cover_image")
        if cover_file and cover_file.filename:
            fname = secure_filename(cover_file.filename)
            cover_file.save(os.path.join(UPLOAD_FOLDER_COVERS, fname))
            cover_path = f"covers/{fname}"

        # Insert manga entry into books table
        conn = get_conn()
        c = conn.cursor()
        c.execute("""
        INSERT INTO books (title, author, category, cover_path, description, book_type, uploader_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (title, author, category, cover_path, description, book_type, uploader_id))
        conn.commit()

        # Get the newly created manga ID
        manga_id = c.lastrowid

        # Handle first chapter upload
        chapter_file = request.files.get("chapter_file")
        if chapter_file and chapter_file.filename:
            ext = chapter_file.filename.rsplit(".", 1)[-1].lower()
            if ext in ALLOWED_PDF:
                pdf_filename = secure_filename(chapter_file.filename)
                chapter_file.save(os.path.join(UPLOAD_FOLDER_PDF, pdf_filename))

                # Insert chapter 1
                c.execute("""
                INSERT INTO chapters (manga_id, chapter_num, title, pdf_filename)
                VALUES (?, ?, ?, ?)
            """, (manga_id, 1, f"Chapter 1", pdf_filename))
                conn.commit()

        conn.close()

        flash("Manga series created successfully. You can add more chapters anytime.", "success")
        return redirect(url_for("manga"))


# ---------- Edit / Delete Book ----------
@app.route("/book/<int:id>/edit", methods=["GET", "POST"])
@role_required("admin", "publisher")
def edit_book(id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_conn()
    c = conn.cursor()

    # pull everything we need, including cover + uploader
    c.execute("""
        SELECT id, title, author, category,
               pdf_filename, audio_filename, cover_path, uploader_id
        FROM books
        WHERE id = ?
    """, (id,))
    row = c.fetchone()

    if not row:
        conn.close()
        flash("Book not found.", "danger")
        return redirect(url_for("home"))

    book = {
        "id": row[0],
        "title": row[1],
        "author": row[2],
        "category": row[3],
        "pdf_filename": row[4],
        "audio_filename": row[5],
        "cover_path": row[6],
        "uploader_id": row[7],
    }

    # --- permission: only admin or the publisher who uploaded it ---
    user_id = session["user_id"]
    role = session.get("role")
    if not (role == "admin" or (book["uploader_id"] and book["uploader_id"] == user_id)):
        conn.close()
        flash("You are not allowed to edit this book.", "danger")
        return redirect(url_for("view_book", id=id))

    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        author = (request.form.get("author") or "").strip()
        category = (request.form.get("category") or "").strip()

        if not title:
            flash("Title is required.", "danger")
            conn.close()
            return redirect(url_for("edit_book", id=id))

        # Start with existing values
        pdf_filename = book["pdf_filename"]
        audio_filename = book["audio_filename"]
        cover_path = book["cover_path"]

        # ----- PDF file (optional replacement) -----
        pdf_file = request.files.get("pdf_file")
        if pdf_file and pdf_file.filename:
            ext = pdf_file.filename.rsplit(".", 1)[-1].lower()
            if ext in ALLOWED_PDF:
                pdf_filename = secure_filename(pdf_file.filename)
                pdf_file.save(os.path.join(UPLOAD_FOLDER_PDF, pdf_filename))
            else:
                flash("PDF must be a .pdf file.", "danger")

        # ----- Audio file (optional replacement) -----
        audio_file = request.files.get("audio_file")
        if audio_file and audio_file.filename:
            ext = audio_file.filename.rsplit(".", 1)[-1].lower()
            if ext in ALLOWED_AUDIO:
                audio_filename = secure_filename(audio_file.filename)
                audio_file.save(os.path.join(UPLOAD_FOLDER_AUDIO, audio_filename))
            else:
                flash("Audio must be a .mp3 file.", "danger")

        # ----- Cover image (optional replacement) -----
        cover_file = request.files.get("cover_file")
        if cover_file and cover_file.filename:
            fname = secure_filename(cover_file.filename)
            cover_file.save(os.path.join(UPLOAD_FOLDER_COVERS, fname))
            cover_path = f"covers/{fname}"   # relative to /static

        # Save everything back
        c.execute("""
            UPDATE books
               SET title = ?,
                   author = ?,
                   category = ?,
                   pdf_filename = ?,
                   audio_filename = ?,
                   cover_path = ?
             WHERE id = ?
        """, (title, author, category, pdf_filename, audio_filename, cover_path, id))

        conn.commit()
        conn.close()
        flash("Book updated successfully.", "success")
        return redirect(url_for("view_book", id=id))

    # GET: show the form
    conn.close()
    return render_template("edit_book.html", book=book)


@app.post("/book/<int:id>/delete")
@role_required("admin", "publisher")
def delete_book(id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, uploader_id FROM books WHERE id=?", (id,))
    row = c.fetchone()

    if not row:
        conn.close()
        flash("Book not found.", "danger")
        return redirect(url_for("home"))

    book_id, uploader_id = row
    user_id = session["user_id"]
    role    = session.get("role")

    # Delete permission:
    # - admin: can delete any book
    # - publisher: can delete only books they uploaded
    allowed = False
    if role == "admin":
        allowed = True
    elif role == "publisher":
        if uploader_id is not None and uploader_id == user_id:
            allowed = True

    if not allowed:
        conn.close()
        flash("You are not allowed to delete this book.", "danger")
        return redirect(url_for("view_book", id=id))

    c.execute("DELETE FROM history   WHERE book_id=?", (book_id,))
    c.execute("DELETE FROM watchlist WHERE book_id=?", (book_id,))
    c.execute("DELETE FROM books     WHERE id=?", (book_id,))
    conn.commit()
    conn.close()

    flash("Book deleted successfully.", "success")
    return redirect(url_for("my_uploads"))


# ---------- Profile ----------
@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT books.title, books.category, history.date_read, books.author, books.cover_path
        FROM history
        JOIN books ON history.book_id = books.id
        WHERE history.user_id = ?
        ORDER BY history.date_read DESC
        LIMIT 50
    """, (user_id,))
    hist = c.fetchall()
    conn.close()

    total_read = len(hist)
    fav_genre = "None yet"
    if total_read:
        cats = [row[1] for row in hist if row[1]]
        fav_genre = Counter(cats).most_common(1)[0][0] if cats else "None yet"

    seen = set()
    currently_reading = []
    for title, cat, dt, author, cover in hist:
        if title not in seen:
            currently_reading.append({"title": title, "author": author, "progress": 25, "cover": cover})
            seen.add(title)
        if len(currently_reading) >= 3:
            break

    recent_finished = []
    for r in hist[:6]:
        # r = (title, category, date_read, author, cover_path)
        recent_finished.append({"title": r[0], "author": r[3], "cover": r[4]})

    recent_activity = [
        {"icon": "fa-check-circle", "text": f"Finished reading <strong>{t}</strong>", "when": d or ""}
        for t, _, d, _, _ in hist[:7]
    ]

    return render_template(
        "profile.html",
        username=session.get("username"),
        count=total_read,
        fav=fav_genre,
        pages_read=None,
        avg_rating=None,
        currently_reading=currently_reading,
        recent_finished=recent_finished,
        recent_activity=recent_activity
    )


# ---------- Watchlist ----------
@app.route("/watchlist")
def watchlist():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_conn()
    c = conn.cursor()
    rows = c.execute("""
        SELECT b.id, b.title, b.author, COALESCE(b.category, 'General'),
               b.pdf_filename, b.audio_filename, b.cover_path,
               w.status, w.progress, w.created_at
        FROM watchlist w
        JOIN books b ON b.id = w.book_id
        WHERE w.user_id = ?
        ORDER BY datetime(w.created_at) DESC
    """, (session["user_id"],)).fetchall()
    
    # Get unique categories from watchlist
    categories = sorted(set([row[3] for row in rows]))
    
    conn.close()

    featured_books = [
        {"id": r[0], "title": r[1], "author": r[2], "category": r[3], "progress": r[8] or 0, "cover": r[6], "status": r[7]}
        for r in rows[:3]
    ]
    table_books = [
        {"id": r[0], "title": r[1], "author": r[2], "category": r[3], "year": "", "rating": 4, "cover": r[6], "status": r[7], "progress": r[8]}
        for r in rows
    ]
    return render_template("watchlist.html", featured_books=featured_books, table_books=table_books, categories=categories)


@app.post("/watchlist/add")
def watchlist_add():
    if "user_id" not in session:
        return redirect(url_for("login"))
    book_id = request.form.get("book_id", "").strip()
    if not book_id.isdigit():
        return redirect(url_for("home"))
    status = (request.form.get("status") or "planned").strip()
    try:
        progress = int(request.form.get("progress") or 0)
    except ValueError:
        progress = 0
    progress = max(0, min(progress, 100))

    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT 1 FROM books WHERE id=?", (book_id,))
    if not c.fetchone():
        conn.close()
        return redirect(url_for("home"))
    try:
        c.execute(
    "UPDATE watchlist SET status=?, progress=? WHERE user_id=? AND book_id=?",
    (status, progress, session["user_id"], book_id)
)

    except sqlite3.IntegrityError:
        # Fallback: attempt same update if integrity error (keep behavior)
        c.execute(
    "UPDATE watchlist SET status=?, progress=? WHERE user_id=? AND book_id=?",
    (status, progress, session["user_id"], book_id)
)

    conn.commit()
    conn.close()
    return redirect(url_for("watchlist"))


@app.post("/watchlist/update")
def watchlist_update():
    if "user_id" not in session:
        return redirect(url_for("login"))
    book_id_raw = request.form.get("book_id", "").strip()
    try:
       book_id = int(book_id_raw)
    except ValueError:
       flash("Invalid book id submitted.", "danger")
       return redirect(url_for("home"))

    status = (request.form.get("status") or "").strip() or None
    progress = request.form.get("progress")
    progress_val = None
    if progress not in (None, ""):
        try:
            progress_val = max(0, min(100, int(progress)))
        except ValueError:
            progress_val = None

    conn = get_conn()
    c = conn.cursor()
    if status is not None and progress_val is not None:
        c.execute(
    "UPDATE watchlist SET status=?, progress=? WHERE user_id=? AND book_id=?",
    (status, progress_val, session["user_id"], book_id)
)

    elif status is not None:
        c.execute(
    "UPDATE watchlist SET status=?, progress=? WHERE user_id=? AND book_id=?",
    (status, progress_val, session["user_id"], book_id)
)

    elif progress_val is not None:
        c.execute(
    "UPDATE watchlist SET status=?, progress=? WHERE user_id=? AND book_id=?",
    (status, progress_val, session["user_id"], book_id)
)

    conn.commit()
    conn.close()
    return redirect(url_for("watchlist"))


@app.post("/watchlist/remove")
def watchlist_remove():
    if "user_id" not in session:
        return redirect(url_for("login"))
    book_id = request.form.get("book_id", "").strip()
    if not book_id.isdigit():
        return redirect(url_for("watchlist"))
    conn = get_conn()
    c = conn.cursor()
    # Remove from watchlist
    c.execute(
    "DELETE FROM watchlist WHERE user_id=? AND book_id=?",
    (session["user_id"], book_id)
    )

    conn.commit()
    conn.close()
    return redirect(url_for("watchlist"))

@app.post("/watchlist/book/<int:book_id>")
def watchlist_book(book_id):
    """Add, update, or remove a single book in the user's watchlist
    from the book detail page.
    """
    if "user_id" not in session:
        return redirect(url_for("login"))

    # which status was chosen in the dropdown
    status = (request.form.get("status") or "").strip()

    conn = sqlite3.connect("library.db")
    c = conn.cursor()

    # make sure the book exists
    c.execute("SELECT 1 FROM books WHERE id=?", (book_id,))
    if not c.fetchone():
        conn.close()
        flash("Book not found.", "danger")
        return redirect(url_for("home"))

    user_id = session["user_id"]

    # if status empty or 'remove' => delete from watchlist
    if not status or status.lower() == "remove":
        c.execute(
            "DELETE FROM watchlist WHERE user_id=? AND book_id=?",
            (user_id, book_id),
        )
        conn.commit()
        conn.close()
        return redirect(url_for("view_book", id=book_id))

    # normalise status to lowercase for storage
    status = status.lower()

    # upsert behaviour: update if exists, else insert
    c.execute(
        "SELECT id, progress FROM watchlist WHERE user_id=? AND book_id=?",
        (user_id, book_id),
    )
    row = c.fetchone()
    if row:
        c.execute(
            "UPDATE watchlist SET status=? WHERE user_id=? AND book_id=?",
            (status, user_id, book_id),
        )
    else:
        c.execute(
            "INSERT INTO watchlist (user_id, book_id, status, progress) VALUES (?, ?, ?, ?)",
            (user_id, book_id, status, 0),
        )

    conn.commit()
    conn.close()
    return redirect(url_for("view_book", id=book_id))

@app.route("/manga")
def manga():
    if "user_id" not in session:
        return redirect(url_for("login"))

    selected = (request.args.get("category") or "").strip()
    q = (request.args.get("q") or "").strip()

    conn = get_conn()
    c = conn.cursor()

    # Get manga categories
    c.execute("""
        SELECT DISTINCT COALESCE(category,'General')
        FROM books
        WHERE COALESCE(book_type,'book')='manga'
        ORDER BY 1
    """)
    categories = [row[0] for row in c.fetchall()]

    # Build query for manga
    base_sql = """
        SELECT id, title, author, COALESCE(category,'General') AS category,
               pdf_filename, audio_filename, cover_path
        FROM books
        WHERE COALESCE(book_type,'book')='manga'
    """
    params = []

    if selected:
        base_sql += " AND COALESCE(category,'General') = ?"
        params.append(selected)

    if q:
        base_sql += " AND (title LIKE ? OR author LIKE ?)"
        search_term = f"%{q}%"
        params.extend([search_term, search_term])

    base_sql += " ORDER BY datetime(created_at) DESC"

    c.execute(base_sql, params)
    mangas = c.fetchall()
    conn.close()

    return render_template(
        "manga.html",
        mangas=mangas,
        categories=categories,
        selected_category=selected,
        q=q,
        body_class="manga-theme"
    )


@app.route("/manga/read/<int:id>")
def read_manga(id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_conn()
    c = conn.cursor()

    # Fetch manga details
    c.execute("""
        SELECT id, title, author, category, pdf_filename, cover_path, book_type
        FROM books
        WHERE id = ? AND COALESCE(book_type, 'book') = 'manga'
    """, (id,))
    manga = c.fetchone()

    if not manga:
        conn.close()
        flash("Manga not found.", "danger")
        return redirect(url_for("manga"))

    # Get all manga for series list (same author or category)
    c.execute("""
        SELECT id, title, author
        FROM books
        WHERE COALESCE(book_type, 'book') = 'manga'
        ORDER BY datetime(created_at) DESC
        LIMIT 10
    """)
    related_manga = c.fetchall()

    conn.close()

    return render_template(
        "manga_reader.html",
        manga=manga,
        related_manga=related_manga
    )


# ---------- Upload Chapter (For Existing Manga) ----------
@app.route("/manga/<int:manga_id>/upload-chapter", methods=["GET", "POST"])
@role_required("admin", "publisher")
def upload_chapter(manga_id):
    if request.method == "GET":
        # Show form to upload chapter
        conn = get_conn()
        c = conn.cursor()
        c.execute("""
            SELECT id, title, author
            FROM books
            WHERE id = ? AND COALESCE(book_type, 'book') = 'manga'
        """, (manga_id,))
        manga = c.fetchone()

        if not manga:
            conn.close()
            flash("Manga not found.", "danger")
            return redirect(url_for("manga"))

        # Get existing chapters
        c.execute("""
            SELECT chapter_num, title
            FROM chapters
            WHERE manga_id = ?
            ORDER BY chapter_num ASC
        """, (manga_id,))
        chapters = c.fetchall()
        conn.close()

        return render_template("upload_chapter.html", manga=manga, chapters=chapters)

    # POST - upload chapter
    chapter_num = request.form.get("chapter_num", "").strip()
    chapter_title = request.form.get("chapter_title", f"Chapter {chapter_num}").strip()
    chapter_file = request.files.get("chapter_file")

    if not chapter_num or not chapter_file or not chapter_file.filename:
        flash("Chapter number and PDF file are required.", "danger")
        return redirect(url_for("upload_chapter", manga_id=manga_id))

    try:
        chapter_num = int(chapter_num)
    except ValueError:
        flash("Chapter number must be a number.", "danger")
        return redirect(url_for("upload_chapter", manga_id=manga_id))

    if chapter_num < 1:
        flash("Chapter number must be at least 1.", "danger")
        return redirect(url_for("upload_chapter", manga_id=manga_id))

    # Check if chapter already exists
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM chapters WHERE manga_id = ? AND chapter_num = ?", (manga_id, chapter_num))
    existing = c.fetchone()

    if existing:
        conn.close()
        flash(f"Chapter {chapter_num} already exists. Please use a different number.", "danger")
        return redirect(url_for("upload_chapter", manga_id=manga_id))

    # Verify manga exists
    c.execute("""
        SELECT id
        FROM books
        WHERE id = ? AND COALESCE(book_type, 'book') = 'manga'
    """, (manga_id,))
    if not c.fetchone():
        conn.close()
        flash("Manga not found.", "danger")
        return redirect(url_for("manga"))

    # Save chapter PDF
    ext = chapter_file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_PDF:
        conn.close()
        flash("Chapter file must be a PDF.", "danger")
        return redirect(url_for("upload_chapter", manga_id=manga_id))

    pdf_filename = secure_filename(chapter_file.filename)
    chapter_file.save(os.path.join(UPLOAD_FOLDER_PDF, pdf_filename))

    # Insert chapter
    c.execute("""
        INSERT INTO chapters (manga_id, chapter_num, title, pdf_filename)
        VALUES (?, ?, ?, ?)
    """, (manga_id, chapter_num, chapter_title, pdf_filename))
    conn.commit()
    conn.close()

    flash(f"Chapter {chapter_num} uploaded successfully!", "success")
    return redirect(url_for("upload_chapter", manga_id=manga_id))


# ---------- About (Team) ----------
@app.route("/about")
def about():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_conn()
    c = conn.cursor()
    rows = c.execute("""
        SELECT full_name, role, bio, avatar_path, initials
        FROM team
        ORDER BY id
    """).fetchall()
    conn.close()

    people = []
    for full, role, bio, avatar_path, initials in rows:
        people.append({
            "name": full,
            "role": role or "Developer",
            "bio": bio or "Member of the NOVUS project.",
            "initials": (initials or "".join(s[0] for s in full.split()[:2]).upper()),
            "avatar": url_for("static", filename=avatar_path)
                      if avatar_path else url_for("static", filename="img/person.png"),
        })
    return render_template("about.html", people=people)


# ---------- My Uploads ----------
@app.route("/my_uploads")
@role_required("admin", "publisher")
def my_uploads():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    role = session.get("role")

    conn = get_conn()
    c = conn.cursor()

    if role == "admin":
        c.execute("""
            SELECT id, title, author,
                   COALESCE(category,'General') AS category,
                   pdf_filename,
                   audio_filename,
                   cover_path,
                   created_at,
                   COALESCE(book_type, 'book') AS book_type
            FROM books
            ORDER BY datetime(created_at) DESC
        """)
    else:
        c.execute("""
            SELECT id, title, author,
                   COALESCE(category,'General') AS category,
                   pdf_filename,
                   audio_filename,
                   cover_path,
                   created_at,
                   COALESCE(book_type, 'book') AS book_type
            FROM books
            WHERE uploader_id = ?
            ORDER BY datetime(created_at) DESC
        """, (user_id,))
    books = c.fetchall()

    # Fetch chapter counts for manga
    manga_chapters = {}
    for book in books:
        if book[8] == 'manga':  # book_type
            c.execute("""
                SELECT COUNT(*) FROM chapters WHERE manga_id = ?
            """, (book[0],))
            count = c.fetchone()[0]
            manga_chapters[book[0]] = count

    conn.close()

    return render_template("my_uploads.html", books=books, is_admin=(role == "admin"), manga_chapters=manga_chapters)


# ---------- Team Admin ----------
# ---------- TEAM ADMIN ----------

@app.route("/admin/team", methods=["GET", "POST"])
@admin_required
def team_admin():
    conn = get_conn()
    c = conn.cursor()

    if request.method == "POST":
        full_name = (request.form.get("full_name") or "").strip()
        role      = (request.form.get("role") or "").strip() or "Developer"
        bio       = (request.form.get("bio") or "").strip() or "Member of the NOVUS project."
        initials  = "".join([p[0] for p in full_name.split()[:2]]).upper() if full_name else ""

        # optional avatar upload
        avatar_rel = None
        file = request.files.get("avatar")
        if file and file.filename:
            os.makedirs(os.path.join(app.root_path, "static", "img", "team"), exist_ok=True)
            fname = secure_filename(file.filename)
            abs_path = os.path.join(app.root_path, "static", "img", "team", fname)
            file.save(abs_path)
            avatar_rel = f"img/team/{fname}"

        c.execute(
            """
            INSERT INTO team(full_name, role, bio, avatar_path, initials, created_at)
            VALUES (?, ?, ?, ?, ?, DATETIME('now'))
            """,
            (full_name, role, bio, avatar_rel, initials),
        )
        conn.commit()
        conn.close()
        flash("Team member added.", "success")
        return redirect(url_for("team_admin"))

    # GET: load members and render page
    members = c.execute(
        "SELECT id, full_name, role, bio, avatar_path FROM team ORDER BY id"
    ).fetchall()
    conn.close()
    return render_template("team_admin.html", members=members)

@app.route("/admin/users")
@admin_required
def admin_users():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT id,
        username,
        role,
        CASE
        WHEN role='admin' THEN 0
        ELSE COALESCE(is_banned,0)
        END AS is_banned
        FROM users
        ORDER BY (role='admin') DESC, username COLLATE NOCASE
        """)
    users = c.fetchall()
    conn.close()
    return render_template("user_management.html", users=users)


@app.post("/admin/users/<int:user_id>/ban")
@admin_required
def ban_user(user_id):
    if user_id == session.get("user_id"):
        flash("You can't ban yourself.", "danger")
        return redirect(url_for("admin_users"))

    conn = get_conn()
    c = conn.cursor()
    # Prevent banning admins
    c.execute("UPDATE users SET is_banned=1 WHERE id=? AND role!='admin'", (user_id,))
    conn.commit()
    conn.close()
    flash("User banned.", "success")
    return redirect(url_for("admin_users"))


@app.post("/admin/users/<int:user_id>/unban")
@admin_required
def unban_user(user_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE users SET is_banned=0 WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
    flash("User unbanned.", "success")
    return redirect(url_for("admin_users"))

@app.post("/admin/users/<int:user_id>/ban")
@admin_required
def user_ban(user_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE users SET status='banned' WHERE id=? AND role!='admin'", (user_id,))
    conn.commit()
    conn.close()
    flash("User has been banned (if not admin).", "warning")
    return redirect(url_for("user_management"))


@app.post("/admin/users/<int:user_id>/unban")
@admin_required
def user_unban(user_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE users SET status='active' WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
    flash("User has been unbanned.", "success")
    return redirect(url_for("user_management"))



@app.post("/admin/users/<int:user_id>/delete")
@admin_required
def user_delete(user_id):
    # prevent deleting self or other admins for safety
    current_id = session.get("user_id")
    conn = get_conn()
    c = conn.cursor()

    c.execute("SELECT role FROM users WHERE id=?", (user_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        flash("User not found.", "danger")
        return redirect(url_for("user_admin"))

    if row[0] == "admin" or user_id == current_id:
        conn.close()
        flash("You cannot delete this admin user.", "danger")
        return redirect(url_for("user_admin"))

    # optional: clean up their reviews, history, watchlist
    c.execute("DELETE FROM reviews WHERE user_id=?", (user_id,))
    c.execute("DELETE FROM history WHERE user_id=?", (user_id,))
    c.execute("DELETE FROM watchlist WHERE user_id=?", (user_id,))
    c.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
    flash("User deleted.", "success")
    return redirect(url_for("user_management"))


    conn = get_conn()
    c = conn.cursor()
    members = c.execute("""
        SELECT id, full_name, role, bio, avatar_path
        FROM team
        ORDER BY id
    """).fetchall()
    conn.close()
    return render_template("team_admin.html", members=members)


@app.post("/admin/team/delete/<int:member_id>")
@admin_required
def team_delete(member_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM team WHERE id=?", (member_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("team_admin"))

@app.route("/admin/users")
@admin_required
def user_management():
    conn = get_conn()
    c = conn.cursor()

    # all users
    c.execute("SELECT id, username, role FROM users ORDER BY id")
    users = c.fetchall()

    # pending publisher requests
    c.execute("""
        SELECT r.id, u.username, r.requested_role, r.created_at
        FROM role_requests r
        JOIN users u ON u.id = r.user_id
        WHERE r.status = 'pending'
        ORDER BY r.created_at ASC
    """)
    pending = c.fetchall()

    conn.close()
    return render_template("user_management.html", users=users, pending=pending)

@app.post("/admin/users/approve/<int:req_id>")
@admin_required
def approve_publisher(req_id):
    conn = get_conn()
    c = conn.cursor()

    # find request + user_id
    c.execute("""
        SELECT user_id, requested_role
        FROM role_requests
        WHERE id = ? AND status = 'pending'
    """, (req_id,))
    row = c.fetchone()

    if not row:
        conn.close()
        flash("Request not found or already processed.", "warning")
        return redirect(url_for("user_management"))

    user_id, requested_role = row

    # update user role
    c.execute("UPDATE users SET role = ? WHERE id = ?", (requested_role, user_id))

    # mark request as approved
    c.execute(
        "UPDATE role_requests SET status = 'approved' WHERE id = ?",
        (req_id,),
    )

    conn.commit()
    conn.close()

    flash(f"User upgraded to {requested_role}.", "success")
    return redirect(url_for("user_management"))


# -------------------- FAQ ROUTE --------------------
@app.route("/faq")
def faq():
    """Display FAQ & Guidelines page"""
    return render_template("faq.html")


# -------------------- MAIN --------------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)

# Ensure DB is initialized exactly once when the app receives requests
_db_init_done = False
@app.before_request
def _ensure_db_initialized():
    global _db_init_done
    if not _db_init_done:
        try:
            init_db()
        except Exception:
            pass
        _db_init_done = True
