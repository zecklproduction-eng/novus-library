from flask import (
    Flask, render_template, request, redirect,
    session, url_for, flash, jsonify, make_response
)
import sqlite3
from datetime import datetime
from datetime import timedelta
from collections import Counter
import os
import logging
from logging.handlers import RotatingFileHandler
from werkzeug.utils import secure_filename
UPLOAD_FOLDER = os.path.join("static", "uploads", "avatars")
ALLOWED_EXTS = {"png", "jpg", "jpeg", "webp"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Import AI error handling
import ai_error_fixes

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTS


# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not required

try:
    import requests
    REQUESTS_AVAILABLE = True
except Exception:
    requests = None
    REQUESTS_AVAILABLE = False
    print('Warning: Python package "requests" not found. Optional features (OpenAI calls, external tests) will be disabled. Install with: pip install requests')
from werkzeug.utils import secure_filename
from functools import wraps
try:
    from pdf2image import convert_from_path
    PDF_EXTRACTION_AVAILABLE = True
except ImportError:
    PDF_EXTRACTION_AVAILABLE = False
    print('Warning: pdf2image not available. PDF to image conversion will be disabled. Install with: pip install pdf2image')

try:
    from authlib.integrations.flask_client import OAuth
    AUTHLIB_AVAILABLE = True
except ImportError:
    OAuth = None
    AUTHLIB_AVAILABLE = False
    print("Warning: Authlib not found. OAuth features disabled.")

# -------------------- PATHS / CONFIG --------------------
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_ROOT, "library.db")

UPLOAD_FOLDER_PDF    = os.path.join(APP_ROOT, "static", "books")
UPLOAD_FOLDER_AUDIO  = os.path.join(APP_ROOT, "static", "audio")
UPLOAD_FOLDER_COVERS = os.path.join(APP_ROOT, "static", "covers")
UPLOAD_FOLDER_MANGA  = os.path.join(APP_ROOT, "static", "manga")

os.makedirs(UPLOAD_FOLDER_PDF, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_AUDIO, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_COVERS, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_MANGA, exist_ok=True)

ALLOWED_PDF   = {"pdf"}
ALLOWED_AUDIO = {"mp3"}
ALLOWED_IMG   = {"jpg", "jpeg", "png"}

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "novus_secret_key")

# OAuth Configuration
if AUTHLIB_AVAILABLE:
    oauth = OAuth(app)
    # Google
    oauth.register(
        name='google',
        client_id=os.environ.get('GOOGLE_CLIENT_ID'),
        client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
        access_token_url='https://accounts.google.com/o/oauth2/token',
        access_token_params=None,
        authorize_url='https://accounts.google.com/o/oauth2/auth',
        authorize_params=None,
        api_base_url='https://www.googleapis.com/oauth2/v1/',
        client_kwargs={'scope': 'openid email profile'},
    )
    # Facebook
    oauth.register(
        name='facebook',
        client_id=os.environ.get('FACEBOOK_CLIENT_ID'),
        client_secret=os.environ.get('FACEBOOK_CLIENT_SECRET'),
        access_token_url='https://graph.facebook.com/oauth/access_token',
        access_token_params=None,
        authorize_url='https://www.facebook.com/dialog/oauth',
        authorize_params=None,
        api_base_url='https://graph.facebook.com/',
        client_kwargs={'scope': 'email'},
    )

# Configure file upload limits
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB limit

# File size limits (in bytes)
MAX_PDF_SIZE = 50 * 1024 * 1024    # 50MB for PDFs
MAX_AUDIO_SIZE = 100 * 1024 * 1024 # 100MB for audio files
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB for images

# -------------------- LOGGING CONFIGURATION --------------------
# Create logs directory if it doesn't exist
logs_dir = os.path.join(APP_ROOT, "logs")
os.makedirs(logs_dir, exist_ok=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('novus')

# File handler for all logs
file_handler = RotatingFileHandler(
    os.path.join(logs_dir, 'novus.log'),
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)

# Console handler for development
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)
console_formatter = logging.Formatter('%(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)

# Add handlers to logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Create system logger instance
system_logger = logging.getLogger('novus.system')

@app.get("/billing/esewa-success")
def esewa_payment_success():
    """Handle eSewa payment success callback"""
    if "user_id" not in session:
        return redirect(url_for("login"))

    # Get the pending plan from session
    pending_plan = session.get("pending_plan")
    uid = session.get("user_id")

    if not pending_plan or pending_plan not in {"pro", "ultimate"}:
        flash("Payment verification failed.", "danger")
        return redirect(url_for("profile"))

    # Apply the plan based on type
    expires_at = None
    if pending_plan == "pro":
        expires_at = (datetime.utcnow() + timedelta(days=30)).isoformat()
    elif pending_plan == "ultimate":
        expires_at = None  # Forever

    # Update user plan in database
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE users SET plan=?, plan_expires_at=? WHERE id=?", (pending_plan, expires_at, uid))
    conn.commit()
    conn.close()

    # Update session
    session["plan"] = pending_plan
    session["plan_expires_at"] = expires_at
    
    # Clear pending plan data
    session.pop("pending_plan", None)
    session.pop("pending_plan_amount", None)
    session.pop("pending_plan_user_id", None)

    flash(f"Payment successful! Plan upgraded to {pending_plan}.", "success")
    return redirect(url_for("profile"))

@app.get("/billing/checkout")
def billing_checkout():
    if "user_id" not in session:
        return redirect(url_for("login"))

    # NOTE: This is a simplified demo flow (no Stripe). In production, replace
    # with a proper payment provider checkout and webhooks to confirm payment.
    plan = (request.args.get("plan", "pro") or "pro").strip().lower()
    if plan not in {"basic", "pro", "ultimate"}:
        flash("Invalid plan selected.", "danger")
        return redirect(url_for("profile"))

    uid = session.get("user_id")
    if not uid:
        return redirect(url_for("login"))

    # For demo: apply the plan immediately. Pro = 30 days from now, Ultimate = forever (NULL)
    expires_at = None
    if plan == "pro":
        expires_at = (datetime.utcnow() + timedelta(days=30)).isoformat()
    elif plan == "basic":
        expires_at = None
    elif plan == "ultimate":
        expires_at = None

    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE users SET plan=?, plan_expires_at=? WHERE id=?", (plan, expires_at, uid))
    conn.commit()
    conn.close()

    # For basic plan, apply immediately without payment
    if plan == "basic":
        session["plan"] = plan
        session["plan_expires_at"] = None
        flash(f"Plan updated to {plan}.", "success")
        return redirect(url_for("profile"))

    # For paid plans, redirect to eSewa payment gateway
    plan_amounts = {"pro": 499, "ultimate": 999}
    amount = plan_amounts.get(plan, 0)
    
    if not amount:
        flash("Invalid plan amount.", "danger")
        return redirect(url_for("profile"))

    # Store pending plan temporarily
    session["pending_plan"] = plan
    session["pending_plan_amount"] = amount
    session["pending_plan_user_id"] = uid

    # Build eSewa payment URL
    esewa_url = "https://uat.esewa.com.np/epay/main"
    transaction_id = f"TXN{uid}{int(datetime.utcnow().timestamp())}"
    success_url = url_for("esewa_payment_success", _external=True)
    failure_url = url_for("profile", _external=True)

    params = {
        "amt": amount,
        "psc": 0,
        "pdc": 0,
        "txAmt": amount,
        "total": amount,
        "tAmt": amount,
        "pid": transaction_id,
        "scd": "EPAYTEST",
        "su": success_url,
        "fu": failure_url
    }
    
    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    return redirect(f"{esewa_url}?{query_string}")
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
    c.execute("SELECT COALESCE(is_banned,0), COALESCE(status,'active') FROM users WHERE id=?", (uid,))
    row = c.fetchone()
    conn.close()
    if row:
        is_banned, status = row
        if int(is_banned) == 1 or status == "banned":
            session.clear()
            flash("Your account has been banned.", "danger")
            return redirect(url_for("login"))


# Context processor to make user avatar available globally
@app.context_processor
def inject_user_avatar():
    return {
        'user_avatar': session.get('avatar_url'),
        'user_id': session.get('user_id')
    }


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


def log_system_event(level, category, message, user_id=None, details=None):
    """Log a system event to database and file"""
    try:
        # Log to file
        log_message = f"[{category.upper()}] {message}"
        if user_id:
            log_message += f" (User: {user_id})"

        if level.upper() == 'INFO':
            system_logger.info(log_message)
        elif level.upper() == 'WARNING':
            system_logger.warning(log_message)
        elif level.upper() == 'ERROR':
            system_logger.error(log_message)
        elif level.upper() == 'CRITICAL':
            system_logger.critical(log_message)

        # Log to database
        conn = get_conn()
        c = conn.cursor()

        # Get request info if available
        ip_address = None
        user_agent = None
        try:
            ip_address = request.remote_addr
            user_agent = request.headers.get('User-Agent', '')[:255]  # Truncate if too long
        except RuntimeError:
            # Outside request context
            pass

        details_json = None
        if details:
            import json
            details_json = json.dumps(details)[:1000]  # Limit size

        c.execute("""
            INSERT INTO system_logs (level, category, message, user_id, ip_address, user_agent, details)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (level.upper(), category, message, user_id, ip_address, user_agent, details_json))

        conn.commit()
        conn.close()

    except Exception as e:
        # Don't let logging errors break the app
        print(f"Logging error: {e}")
        pass


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

    # Add description column if it doesn't exist (migration for existing DBs)
    try:
        c.execute("ALTER TABLE books ADD COLUMN description TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    # Add email column if it doesn't exist
    try:
        c.execute("ALTER TABLE users ADD COLUMN email TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    # Add google_id and facebook_id columns
    try:
        c.execute("ALTER TABLE users ADD COLUMN google_id TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE users ADD COLUMN facebook_id TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    # Attempt to create Unique Index on email
    try:
        c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        conn.commit()
    except sqlite3.IntegrityError:
        print("Warning: Could not create unique index on email due to existing duplicates via init_db.")
    except Exception as e:
        print(f"Warning: Issue creating index on email: {e}")

    # Add avatar_url column if it doesn't exist
    try:
        c.execute("ALTER TABLE users ADD COLUMN avatar_url TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass
    # Plan storage
    try:
        c.execute("ALTER TABLE users ADD COLUMN plan TEXT")
        conn.commit()
    except Exception:
      pass

    try:
        c.execute("ALTER TABLE users ADD COLUMN plan_expires_at TEXT")
        conn.commit()
    except Exception:
        pass

    # Ensure existing users have a default plan
    try:
        c.execute("UPDATE users SET plan='basic' WHERE plan IS NULL")
        conn.commit()
    except Exception:
        pass

    # AI summaries cache table
    c.execute("""
        CREATE TABLE IF NOT EXISTS ai_summaries (
            id INTEGER PRIMARY KEY,
            item_type TEXT,
            item_id INTEGER,
            summary TEXT,
            model TEXT,
            created_at TEXT,
            UNIQUE(item_type, item_id)
        )
    """)
    
    # image summaries cache table
    c.execute("""
        CREATE TABLE IF NOT EXISTS image_summaries (
            id INTEGER PRIMARY KEY,
            chapter_id INTEGER,
            page_num INTEGER,
            summary TEXT,
            created_at TEXT DEFAULT (DATETIME('now')),
            UNIQUE(chapter_id, page_num)
        )
    """)

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

    # favorites
    c.execute("""
        CREATE TABLE IF NOT EXISTS favorites (
            id         INTEGER PRIMARY KEY,
            user_id    INTEGER NOT NULL,
            book_id    INTEGER NOT NULL,
            created_at TEXT DEFAULT (DATETIME('now')),
            UNIQUE(user_id, book_id)
        )
    """)

    # reports (user reports on manga/books)
    c.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            manga_id INTEGER,
            reason TEXT,
            created_at TEXT DEFAULT (DATETIME('now'))
        )
    """)

    # user_reports (user reports on other users)
    c.execute("""
        CREATE TABLE IF NOT EXISTS user_reports (
            id INTEGER PRIMARY KEY,
            reporter_id INTEGER NOT NULL,
            reported_user_id INTEGER NOT NULL,
            reason TEXT,
            created_at TEXT DEFAULT (DATETIME('now')),
            FOREIGN KEY (reporter_id) REFERENCES users(id),
            FOREIGN KEY (reported_user_id) REFERENCES users(id)
        )
    """)

    # reviews (book/manga reviews)
    c.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            book_id INTEGER NOT NULL,
            rating INTEGER,
            content TEXT,
            created_at TEXT DEFAULT (DATETIME('now')),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (book_id) REFERENCES books(id)
        )
    """)

    # chapter_reviews (chapter reviews)
    c.execute("""
        CREATE TABLE IF NOT EXISTS chapter_reviews (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            chapter_id INTEGER NOT NULL,
            rating INTEGER,
            content TEXT,
            created_at TEXT DEFAULT (DATETIME('now')),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (chapter_id) REFERENCES chapters(id),
            UNIQUE(user_id, chapter_id)
        )
    """)

    # activity log (track user reading activities)
    c.execute("""
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            book_id INTEGER NOT NULL,
            activity_type TEXT NOT NULL,
            summary_generated INTEGER DEFAULT 0,
            timestamp TEXT DEFAULT (DATETIME('now')),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (book_id) REFERENCES books(id)
        )
    """)

    # system logs (track system events, admin actions, errors)
    c.execute("""
        CREATE TABLE IF NOT EXISTS system_logs (
            id INTEGER PRIMARY KEY,
            level TEXT NOT NULL,  -- INFO, WARNING, ERROR, CRITICAL
            category TEXT NOT NULL,  -- auth, admin, upload, error, system
            message TEXT NOT NULL,
            user_id INTEGER,  -- NULL for system events
            ip_address TEXT,
            user_agent TEXT,
            details TEXT,  -- JSON string for additional data
            timestamp TEXT DEFAULT (DATETIME('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
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
            page_count  INTEGER DEFAULT 0,
            created_at  TEXT DEFAULT (DATETIME('now')),
            FOREIGN KEY (manga_id) REFERENCES books(id),
            UNIQUE(manga_id, chapter_num)
        )
    """)

    # Add page_count column to chapters if it doesn't exist (migration for existing DBs)
    try:
        c.execute("ALTER TABLE chapters ADD COLUMN page_count INTEGER DEFAULT 0")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    # manga characters (for character profiles in reader)
    c.execute("""
        CREATE TABLE IF NOT EXISTS manga_characters (
            id          INTEGER PRIMARY KEY,
            manga_id    INTEGER NOT NULL,
            name        TEXT NOT NULL,
            description TEXT,
            role        TEXT,
            avatar_url  TEXT,
            created_at  TEXT DEFAULT (DATETIME('now')),
            FOREIGN KEY (manga_id) REFERENCES books(id)
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
    books_raw = c.fetchall()
    
    # Get user's favorite book IDs for showing heart icons
    user_favorites = set()
    if "user_id" in session:
        c.execute("SELECT book_id FROM favorites WHERE user_id = ?", (session["user_id"],))
        user_favorites = {row[0] for row in c.fetchall()}
    
    # Add favorite status to each book (as a boolean flag)
    books = []
    for book in books_raw:
        is_favorited = book[0] in user_favorites
        books.append(list(book) + [is_favorited])

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
    # Prevent browser back button from showing login page after logout
    if request.method == "GET" and "user_id" in session:
        return redirect(url_for("home"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        conn = get_conn()
        c = conn.cursor()
        c.execute("""
    SELECT id, username, password, role,
           COALESCE(is_banned,0),
           COALESCE(status,'active'),
           COALESCE(plan,'basic'),
           plan_expires_at,
           COALESCE(avatar_url, NULL) as avatar_url,
           COALESCE(email, NULL) as email
    FROM users
    WHERE username=? AND password=?
""", (username, password))


        user = c.fetchone()
        conn.close()

        if not user:
            # Log failed login attempt
            log_system_event('WARNING', 'auth', f'Failed login attempt for username: {username}')
            return render_template("login.html", error="Invalid username or password.")

        # user[4] = is_banned (0/1), user[5] = status ('active'/'banned')
        if int(user[4]) == 1 or user[5] == "banned":
            # Log banned user login attempt
            log_system_event('WARNING', 'auth', f'Banned user {user[1]} attempted to login', user[0])
            return render_template(
                "login.html",
                error="Your account has been banned. Please contact the administrator."
            )

        session["user_id"] = user[0]
        session["username"] = user[1]
        session["role"] = user[3]
        # Indices: 6=plan, 7=plan_expires_at, 8=avatar_url, 9=email
        session["plan"] = user[6] or "basic"
        session["plan_expires_at"] = user[7]
        session["avatar_url"] = user[8]
        session["email"] = user[9]
        # Make ultimate permanent (no expiry)
        if session["plan"] == "ultimate":
            session["plan_expires_at"] = None

        # Log successful login
        log_system_event('INFO', 'auth', f'User {user[1]} logged in successfully', user[0])

        return redirect(url_for("home"))

    response = make_response(render_template("login.html"))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# ---------- OAuth Routes ----------
@app.route('/login/<provider>')
def oauth_login(provider):
    if not AUTHLIB_AVAILABLE:
        flash("Social login is currently disabled.", "warning")
        return redirect(url_for('login'))
    
    # Create valid callback URL
    redirect_uri = url_for('oauth_callback', provider=provider, _external=True)
    return oauth.create_client(provider).authorize_redirect(redirect_uri)

@app.route('/auth/callback/<provider>')
def oauth_callback(provider):
    if not AUTHLIB_AVAILABLE:
        flash("Social login is currently disabled.", "warning")
        return redirect(url_for('login'))

    client = oauth.create_client(provider)
    try:
        token = client.authorize_access_token()
    except Exception as e:
        log_system_event('ERROR', 'auth', f'OAuth Error: {str(e)}')
        flash("Authentication failed. Please try again.", "danger")
        return redirect(url_for('login'))

    user_info = None
    if provider == 'google':
        user_info = client.get('https://www.googleapis.com/oauth2/v1/userinfo').json()
        email = user_info.get('email')
        provider_user_id = user_info.get('id')
        name = user_info.get('name') or email.split('@')[0]
        avatar_url = user_info.get('picture')
    elif provider == 'facebook':
        user_info = client.get('me?fields=id,name,email,picture').json()
        email = user_info.get('email')
        provider_user_id = user_info.get('id')
        name = user_info.get('name') or email.split('@')[0] if email else 'User'
        # Facebook Logic for Picture
        try:
             avatar_url = user_info['picture']['data']['url']
        except:
             avatar_url = None

    if not email:
        flash("Could not retrieve email from provider. Please register manually.", "danger")
        return redirect(url_for('register'))

    conn = get_conn()
    c = conn.cursor()

    # 1. Try to find by provider ID
    c.execute(f"SELECT id, username, role, plan, plan_expires_at, avatar_url, email FROM users WHERE {provider}_id=?", (provider_user_id,))
    user = c.fetchone()

    if user:
        # User exists via provider ID
        user_id = user[0]
        username = user[1]
        role = user[2]
        plan = user[3]
        plan_exp = user[4]
        db_avatar = user[5]
        
    else:
        # 2. Try to find by Email
        c.execute("SELECT id, username, role, plan, plan_expires_at, avatar_url FROM users WHERE email=?", (email,))
        user_by_email = c.fetchone()
        
        if user_by_email:
            # Link existing account
            user_id = user_by_email[0]
            username = user_by_email[1]
            role = user_by_email[2]
            plan = user_by_email[3]
            plan_exp = user_by_email[4]
            db_avatar = user_by_email[5]
            
            c.execute(f"UPDATE users SET {provider}_id=? WHERE id=?", (provider_user_id, user_id))
            conn.commit()
            log_system_event('INFO', 'auth', f'Linked {provider} account for user {username}')
        else:
            # 3. Create new user
            import secrets
            import string
            
            # Generate unique username
            base_username = name.replace(' ', '').lower()
            username = base_username
            attempt = 1
            while True:
                c.execute("SELECT 1 FROM users WHERE username=?", (username,))
                if not c.fetchone():
                    break
                username = f"{base_username}{attempt}"
                attempt += 1

            # Random secure password
            alphabet = string.ascii_letters + string.digits
            password = ''.join(secrets.choice(alphabet) for i in range(16))
            
            # Role defaults to reader
            role = 'reader'

            c.execute(f"INSERT INTO users (username, email, password, role, {provider}_id, avatar_url) VALUES (?, ?, ?, ?, ?, ?)",
                      (username, email, password, role, provider_user_id, avatar_url))
            conn.commit()
            
            user_id = c.lastrowid
            plan = 'basic'
            plan_exp = None
            db_avatar = avatar_url
            log_system_event('INFO', 'auth', f'Created new user {username} via {provider}')

    conn.close()

    # Log user in
    session["user_id"] = user_id
    session["username"] = username
    session["role"] = role
    session["plan"] = plan or "basic"
    session["plan_expires_at"] = plan_exp
    session["avatar_url"] = db_avatar
    session["email"] = email
    
    if session["plan"] == "ultimate":
        session["plan_expires_at"] = None

    log_system_event('INFO', 'auth', f'User {username} logged in via {provider}', user_id)
    return redirect(url_for("home"))

@app.before_request
def refresh_plan():
    uid = session.get("user_id")
    if not uid:
        return
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COALESCE(plan,'basic'), plan_expires_at FROM users WHERE id=?", (uid,))
    row = c.fetchone()
    conn.close()
    if row:
        session["plan"] = row[0] or "basic"
        session["plan_expires_at"] = row[1]
        # compute days left if expiry exists and plan is not ultimate
        session["plan_days_left"] = None
        try:
            if session.get("plan_expires_at") and session.get("plan") != "ultimate":
                exp = session.get("plan_expires_at")
                # parse ISO timestamps
                try:
                    exp_dt = datetime.fromisoformat(exp)
                except Exception:
                    # fallback if stored as plain date
                    exp_dt = datetime.strptime(exp, "%Y-%m-%d")
                delta = exp_dt - datetime.utcnow()
                days_left = max(0, delta.days)
                session["plan_days_left"] = days_left
        except Exception:
            session["plan_days_left"] = None

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
        
        # Unique email check
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT 1 FROM users WHERE email=?", (email,))
        if c.fetchone():
            conn.close()
            flash("That email is already registered. Please login instead.", "danger")
            return redirect(url_for("register"))
        conn.close()

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
    user_id = session.get("user_id")
    username = session.get("username")
    if user_id:
        log_system_event('INFO', 'auth', f'User {username} logged out', user_id)
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
        "SELECT id, title, author, category, pdf_filename, audio_filename, cover_path, description FROM books WHERE id=?",
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

    # Log activity - always log when user reads/views a book
    try:
        c.execute("""
            INSERT INTO activity_log (user_id, book_id, activity_type)
            VALUES (?, ?, ?)
        """, (user_id, id, 'read'))
        conn.commit()
    except Exception:
        # don't fail the page if logging fails
        pass

    # watchlist entry for this user/book (if any)
    c.execute(
        "SELECT status, progress FROM watchlist WHERE user_id=? AND book_id=?",
        (user_id, id),
    )
    watchlist_row = c.fetchone()
    current_status = watchlist_row[0] if watchlist_row else None

    # Check if book is in favorites
    c.execute(
        "SELECT 1 FROM favorites WHERE user_id=? AND book_id=?",
        (user_id, id),
    )
    is_favorited = c.fetchone() is not None

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
               u.username, u.id, u.avatar_url
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
    top_wishlisted=top_wishlisted,
    is_favorited=is_favorited
)


# ---------- AI Summary Endpoint ----------
@app.route('/ai_summary', methods=['POST'])
def ai_summary():
    """Return a short AI-style summary for provided text.
    POST JSON: { text: string, max_sentences: int (optional) }
    """
    try:
        data = request.get_json() or {}
        
        # Validate request with AI error handling
        is_valid, error_msg = ai_error_fixes.validate_ai_request(data, ['text'])
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        text = (data.get('text') or '').strip()
        try:
            max_sents = int(data.get('max_sentences', 3))
        except Exception:
            max_sents = 3

        if not text:
            return jsonify({'error': 'No text provided.'}), 400

        # Optional caching parameters
        item_type = (data.get('item_type') or '').strip() or None
        try:
            item_id = int(data.get('item_id')) if data.get('item_id') is not None else None
        except Exception:
            item_id = None
        force = bool(data.get('force'))

        # Check cache with optional TTL
        if item_type and item_id and not force:
            conn = get_conn()
            c = conn.cursor()
            c.execute("SELECT id, summary, model, created_at FROM ai_summaries WHERE item_type=? AND item_id=?", (item_type, item_id))
            row = c.fetchone()
            if row:
                rid, summary_text, model_name, created_at = row
                ttl_days = int(os.environ.get('AI_SUMMARY_TTL_DAYS', '0') or '0')
                if ttl_days > 0:
                    try:
                        created_dt = datetime.fromisoformat(created_at)
                        age = datetime.utcnow() - created_dt
                        if age.days >= ttl_days:
                            # expired, remove
                            c.execute("DELETE FROM ai_summaries WHERE id=?", (rid,))
                            conn.commit()
                            row = None
                    except Exception:
                        # if parsing fails, proceed to use cached value
                        pass
            conn.close()
            if row:
                # return cached
                return jsonify({'summary': summary_text, 'cached': True, 'model': model_name, 'cached_at': created_at})

    except Exception as e:
        # Handle any unexpected errors with AI error handling
        error_details = ai_error_fixes.handle_ai_service_error(e, 'AI Summary Service')
        return jsonify({
            'error': error_details['error'],
            'message': error_details.get('retry_after', 'Please try again later'),
            'summary': ai_error_fixes.get_ai_fallback_message()
        }), 500

    def simple_summarize(src, max_sentences=3):
        import re
        src = src.replace('\n', ' ').strip()
        # Split into sentences
        sents = re.split(r'(?<=[.!?])\s+', src)
        # If short text, produce a concise variant rather than returning identical text
        if len(src) < 250:
            if len(sents) == 1:
                # single sentence: truncate to ~30 words
                words = sents[0].split()
                if len(words) <= 30:
                    return sents[0]
                return ' '.join(words[:30]).rstrip() + '…'
            else:
                # multiple sentences: return up to max_sentences sentences
                return ' '.join(sents[:max_sentences])

        # Build frequency table
        words = re.findall(r"\w+", src.lower())
        stopwords = set(["the","and","a","an","of","in","to","is","it","that","for","on","with","as","was","are","by","this","be"])
        freq = {}
        for w in words:
            if w in stopwords or len(w) < 3:
                continue
            freq[w] = freq.get(w, 0) + 1

        scores = []
        for i, s in enumerate(sents):
            s_words = re.findall(r"\w+", s.lower())
            score = sum(freq.get(w, 0) for w in s_words)
            scores.append((i, score, s))

        # Pick top sentences
        top = sorted(scores, key=lambda x: x[1], reverse=True)[:max_sentences]
        top_sorted = sorted(top, key=lambda x: x[0])
        summary = ' '.join(s for (_, _, s) in top_sorted)
        return summary

    # Try using external LLM if configured
    summary = None
    used_model = 'simple'
    OPENAI_KEY = os.environ.get('OPENAI_API_KEY')
    USE_OPENAI = os.environ.get('USE_OPENAI', '0') in ('1', 'true', 'True')

    def call_openai_summary(src, max_sentences=3):
        # ensure requests is available and API key present
        if not REQUESTS_AVAILABLE or not OPENAI_KEY:
            return None, None
        model = os.environ.get('OPENAI_MODEL', 'gpt-3.5-turbo')
        prompt = f"Summarize the following text in {max_sentences} concise sentences:\n\n{src}"
        headers = {'Authorization': f'Bearer {OPENAI_KEY}', 'Content-Type': 'application/json'}
        payload = {
            'model': model,
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': 300,
            'temperature': 0.3,
        }
        try:
            resp = requests.post('https://api.openai.com/v1/chat/completions', json=payload, headers=headers, timeout=10)
            if resp.status_code == 200:
                j = resp.json()
                txt = j['choices'][0]['message']['content'].strip()
                return txt, model
        except Exception as e:
            # Use AI error handling for OpenAI API errors
            error_details = ai_error_fixes.handle_ai_service_error(e, 'OpenAI')
            print(f"OpenAI API Error: {error_details['error']}")
        return None, None

    if OPENAI_KEY and USE_OPENAI:
        txt, model = call_openai_summary(text, max_sents)
        if txt:
            summary = txt
            used_model = model

    if not summary:
        summary = simple_summarize(text, max_sents)
        used_model = 'simple'

    # Store cache if item provided
    if item_type and item_id:
        conn = get_conn()
        c = conn.cursor()
        now = datetime.utcnow().isoformat()
        try:
            c.execute("INSERT OR REPLACE INTO ai_summaries (item_type, item_id, summary, model, created_at) VALUES (?, ?, ?, ?, ?)",
                      (item_type, item_id, summary, used_model, now))
            conn.commit()
        except Exception:
            pass
        finally:
            conn.close()

    return jsonify({'summary': summary, 'cached': False, 'model': used_model})


# ---------- Admin: AI Summaries Management ----------
@app.route('/admin/ai_summaries')
@admin_required
def admin_ai_summaries():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, item_type, item_id, model, created_at, summary FROM ai_summaries ORDER BY created_at DESC")
    rows = c.fetchall()
    conn.close()

    ttl_days = int(os.environ.get('AI_SUMMARY_TTL_DAYS', '0') or '0')
    return render_template('admin_ai_summaries.html', rows=rows, ttl_days=ttl_days)


@app.route('/admin/reports')
@admin_required
def admin_reports():
    conn = get_conn()
    c = conn.cursor()

    # Get users with 2 or more reports
    c.execute("""
        SELECT u.id, u.username, u.email, u.role, COUNT(ur.id) as report_count,
               GROUP_CONCAT(ur.reason, '; ') as reasons,
               MAX(ur.created_at) as latest_report
        FROM users u
        JOIN user_reports ur ON u.id = ur.reported_user_id
        GROUP BY u.id, u.username, u.email, u.role
        HAVING COUNT(ur.id) >= 2
        ORDER BY report_count DESC, latest_report DESC
    """)
    reported_users = c.fetchall()

    # Get all reports for details
    c.execute("""
        SELECT ur.id, ur.reporter_id, ru.username as reporter_name,
               ur.reported_user_id, u.username as reported_name,
               ur.reason, ur.created_at
        FROM user_reports ur
        JOIN users ru ON ur.reporter_id = ru.id
        JOIN users u ON ur.reported_user_id = u.id
        ORDER BY ur.created_at DESC
        LIMIT 100
    """)
    all_reports = c.fetchall()

    conn.close()

    return render_template('admin_reports.html', reported_users=reported_users, all_reports=all_reports)


@app.route('/admin/system_logs')
@admin_required
def admin_system_logs():
    # Get filter parameters
    level_filter = request.args.get('level', '').strip()
    category_filter = request.args.get('category', '').strip()
    limit = int(request.args.get('limit', 100))

    conn = get_conn()
    c = conn.cursor()

    # Build query with filters
    query = """
        SELECT sl.id, sl.level, sl.category, sl.message, sl.user_id, u.username,
               sl.ip_address, sl.timestamp, sl.details
        FROM system_logs sl
        LEFT JOIN users u ON sl.user_id = u.id
    """
    params = []
    conditions = []

    if level_filter:
        conditions.append("sl.level = ?")
        params.append(level_filter.upper())

    if category_filter:
        conditions.append("sl.category = ?")
        params.append(category_filter)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY sl.timestamp DESC LIMIT ?"
    params.append(limit)

    c.execute(query, params)
    logs = c.fetchall()

    # Get unique levels and categories for filter dropdowns
    c.execute("SELECT DISTINCT level FROM system_logs ORDER BY level")
    levels = [row[0] for row in c.fetchall()]

    c.execute("SELECT DISTINCT category FROM system_logs ORDER BY category")
    categories = [row[0] for row in c.fetchall()]

    conn.close()

    return render_template('admin_system_logs.html',
                         logs=logs,
                         levels=levels,
                         categories=categories,
                         current_level=level_filter,
                         current_category=category_filter,
                         limit=limit)


@app.route('/admin/fix_uploaders', methods=['GET', 'POST'])
@admin_required
def admin_fix_uploaders():
    conn = get_conn(); c = conn.cursor()
    if request.method == 'POST':
        data = request.get_json() or {}
        ids = data.get('ids') or []
        try:
            ids = [int(i) for i in ids]
        except Exception:
            conn.close()
            return jsonify({'error': 'invalid ids'}), 400
        if not ids:
            conn.close(); return jsonify({'updated': 0})
        uid = session.get('user_id')
        placeholders = ','.join('?' for _ in ids)
        c.execute(f"UPDATE books SET uploader_id=? WHERE id IN ({placeholders})", tuple([uid]+ids))
        conn.commit(); updated = c.rowcount; conn.close()
        return jsonify({'updated': updated})

    # GET: show books with missing uploader
    c.execute("SELECT id, title, author, created_at FROM books WHERE uploader_id IS NULL ORDER BY created_at DESC")
    rows = c.fetchall()
    conn.close()
    return render_template('admin_fix_uploaders.html', rows=rows)


@app.route('/admin/ai_summaries/clear', methods=['POST'])
@admin_required
def admin_ai_summaries_clear():
    data = request.get_json() or {}
    action = data.get('action')
    conn = get_conn()
    c = conn.cursor()

    if action == 'selected':
        ids = data.get('ids') or []
        if not ids:
            conn.close()
            return jsonify({'deleted': 0})
        # ensure ints
        try:
            ids = [int(i) for i in ids]
        except Exception:
            conn.close()
            return jsonify({'error': 'invalid ids'}), 400

        placeholders = ','.join('?' for _ in ids)
        c.execute(f"DELETE FROM ai_summaries WHERE id IN ({placeholders})", tuple(ids))
        deleted = c.rowcount
        conn.commit()
        conn.close()
        return jsonify({'deleted': deleted})

    elif action == 'expired':
        ttl_days = int(os.environ.get('AI_SUMMARY_TTL_DAYS', '0') or '0')
        if ttl_days <= 0:
            conn.close()
            return jsonify({'deleted': 0, 'error': 'TTL not set or zero'}), 400

        cutoff = datetime.utcnow() - timedelta(days=ttl_days)
        # delete entries older than cutoff
        c.execute("SELECT id, created_at FROM ai_summaries")
        rows = c.fetchall()
        to_delete = []
        for rid, created_at in rows:
            try:
                created_dt = datetime.fromisoformat(created_at)
                if created_dt < cutoff:
                    to_delete.append(rid)
            except Exception:
                # if parsing fails, skip
                continue

        if not to_delete:
            conn.close()
            return jsonify({'deleted': 0})

        placeholders = ','.join('?' for _ in to_delete)
        c.execute(f"DELETE FROM ai_summaries WHERE id IN ({placeholders})", tuple(to_delete))
        deleted = c.rowcount
        conn.commit()
        conn.close()
        return jsonify({'deleted': deleted})

    else:
        conn.close()
        return jsonify({'error': 'unknown action'}), 400



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


@app.post("/chapter/<int:chapter_id>/review")
def add_chapter_review(chapter_id):
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
        # Get manga_id
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT manga_id FROM chapters WHERE id=?", (chapter_id,))
        row = c.fetchone()
        conn.close()
        if row:
            return redirect(url_for("view_chapter", manga_id=row[0], chapter_id=chapter_id))
        else:
            return redirect(url_for("manga"))

    conn = get_conn()
    c = conn.cursor()
    # Get manga_id
    c.execute("SELECT manga_id FROM chapters WHERE id=?", (chapter_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        flash("Chapter not found.", "danger")
        return redirect(url_for("manga"))
    manga_id = row[0]

    # Check if user already reviewed this chapter
    c.execute("SELECT id FROM chapter_reviews WHERE user_id=? AND chapter_id=?", (user_id, chapter_id))
    existing = c.fetchone()
    if existing:
        # Update existing
        c.execute("UPDATE chapter_reviews SET rating=?, content=? WHERE id=?", (rating, content, existing[0]))
    else:
        # Insert new
        c.execute("INSERT INTO chapter_reviews (user_id, chapter_id, rating, content) VALUES (?, ?, ?, ?)", (user_id, chapter_id, rating, content))
    conn.commit()
    conn.close()
    flash("Review added.", "success")
    return redirect(url_for("view_chapter", manga_id=manga_id, chapter_id=chapter_id))


@app.post("/chapter_review/<int:review_id>/delete")
def delete_chapter_review(review_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    role = session.get("role")

    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT user_id, chapter_id FROM chapter_reviews WHERE id=?", (review_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        flash("Review not found.", "danger")
        return redirect(url_for("manga"))

    owner_id, chapter_id = row
    # Get manga_id
    c.execute("SELECT manga_id FROM chapters WHERE id=?", (chapter_id,))
    manga_row = c.fetchone()
    manga_id = manga_row[0] if manga_row else None

    # owner or admin can delete
    if owner_id != user_id and role != "admin":
        conn.close()
        flash("You cannot delete this review.", "danger")
        return redirect(url_for("view_chapter", manga_id=manga_id, chapter_id=chapter_id) if manga_id else url_for("manga"))

    c.execute("DELETE FROM chapter_reviews WHERE id=?", (review_id,))
    conn.commit()
    conn.close()
    flash("Review deleted.", "success")
    return redirect(url_for("view_chapter", manga_id=manga_id, chapter_id=chapter_id) if manga_id else url_for("manga"))


# ---------- Add Book (Admin + Publisher) ----------
@app.route("/add", methods=["GET", "POST"])
@role_required("admin", "publisher")
def add_book():
    if request.method == "GET":
        return render_template("add_book.html")

    title    = (request.form.get("title") or "").strip()
    author   = (request.form.get("author") or "").strip()
    # Handle multiple categories (comma-separated)
    categories_list = request.form.getlist("categories")
    category = ",".join([c.strip() for c in categories_list if c.strip()]) if categories_list else "General"
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
            # Check file size
            if pdf_file.content_length > MAX_PDF_SIZE:
                flash(f"PDF file is too large. Maximum size is {MAX_PDF_SIZE // (1024*1024)}MB.", "danger")
                return redirect(url_for("add_book"))

            ext = pdf_file.filename.rsplit(".", 1)[-1].lower()
            if ext in ALLOWED_PDF:
                pdf_filename = secure_filename(pdf_file.filename)
                pdf_file.save(os.path.join(UPLOAD_FOLDER_PDF, pdf_filename))
            else:
                flash("Digital book must be a .pdf file.", "danger")

        # Audio
        audio_file = request.files.get("audio_file")
        if audio_file and audio_file.filename:
            # Check file size
            if audio_file.content_length > MAX_AUDIO_SIZE:
                flash(f"Audio file is too large. Maximum size is {MAX_AUDIO_SIZE // (1024*1024)}MB.", "danger")
                return redirect(url_for("add_book"))

            ext = audio_file.filename.rsplit(".", 1)[-1].lower()
            if ext in ALLOWED_AUDIO:
                audio_filename = secure_filename(audio_file.filename)
                audio_file.save(os.path.join(UPLOAD_FOLDER_AUDIO, audio_filename))
            else:
                flash("Audiobook must be a .mp3 file.", "danger")

        # Cover
        cover_file = request.files.get("cover_image")
        if cover_file and cover_file.filename:
            # Check file size
            if cover_file.content_length > MAX_IMAGE_SIZE:
                flash(f"Cover image is too large. Maximum size is {MAX_IMAGE_SIZE // (1024*1024)}MB.", "danger")
                return redirect(url_for("add_book"))

            fname = secure_filename(cover_file.filename)
            cover_file.save(os.path.join(UPLOAD_FOLDER_COVERS, fname))
            cover_path = f"covers/{fname}"

        conn = get_conn()
        c = conn.cursor()
        # record uploader_id so the user who created the book can edit it later
        uploader_id = session.get('user_id')
        c.execute("""
        INSERT INTO books (title, author, category, pdf_filename, audio_filename, cover_path, book_type, uploader_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (title, author, category, pdf_filename, audio_filename, cover_path, book_type, uploader_id))
        conn.commit()
        conn.close()

        # Log book upload
        uploader_id = session.get("user_id")
        log_system_event('INFO', 'upload', f'User uploaded book: {title}', uploader_id, {'book_id': c.lastrowid, 'book_type': 'book'})

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
            # Check file size
            if cover_file.content_length > MAX_IMAGE_SIZE:
                flash(f"Cover image is too large. Maximum size is {MAX_IMAGE_SIZE // (1024*1024)}MB.", "danger")
                return redirect(url_for("add_book"))

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

        # Handle first chapter upload - support both PDF and multiple images
        chapter_format = (request.form.get("chapter_format") or "images").lower().strip()
        page_count = 0
        pages_data = None

        if chapter_format == "pdf":
            # Handle PDF upload
            chapter_pdf = request.files.get("chapter_pdf")
            if chapter_pdf and chapter_pdf.filename:
                # Check file size
                if chapter_pdf.content_length > MAX_PDF_SIZE:
                    flash(f"Chapter PDF is too large. Maximum size is {MAX_PDF_SIZE // (1024*1024)}MB.", "danger")
                    return redirect(url_for("add_book"))

                ext = chapter_pdf.filename.rsplit(".", 1)[-1].lower()
                if ext in ALLOWED_PDF:
                    pdf_filename = secure_filename(chapter_pdf.filename)
                    chapter_pdf.save(os.path.join(UPLOAD_FOLDER_PDF, pdf_filename))
                    pages_data = pdf_filename
                    page_count = 1
        else:
            # Handle image uploads (multiple pages)
            chapter_pages = request.files.getlist("chapter_pages")

            if chapter_pages and len(chapter_pages) > 0:
                # Create manga chapter directory
                chapter_dir = os.path.join(UPLOAD_FOLDER_MANGA, f"manga_{manga_id}_ch1")
                os.makedirs(chapter_dir, exist_ok=True)

                page_files = []

                for idx, page_file in enumerate(chapter_pages, 1):
                    if page_file and page_file.filename:
                        # Check file size for each image
                        if page_file.content_length > MAX_IMAGE_SIZE:
                            flash(f"Chapter image '{page_file.filename}' is too large. Maximum size is {MAX_IMAGE_SIZE // (1024*1024)}MB.", "danger")
                            return redirect(url_for("add_book"))

                        ext = page_file.filename.rsplit(".", 1)[-1].lower()
                        if ext in ALLOWED_IMG:
                            # Save with page number for ordering
                            page_filename = f"page_{idx:03d}.{ext}"
                            page_file.save(os.path.join(chapter_dir, page_filename))
                            page_files.append(page_filename)
                            page_count += 1
                
                if page_count > 0:
                    # Store page files info (comma-separated)
                    pages_data = ",".join(page_files)

        if pages_data and page_count > 0:
            # Insert chapter into database
            c.execute("""
                INSERT INTO chapters (manga_id, chapter_num, title, pdf_filename, page_count)
                VALUES (?, ?, ?, ?, ?)
            """, (manga_id, 1, "Chapter 1", pages_data, page_count))
            conn.commit()

        conn.close()

        # Log manga upload
        uploader_id = session.get("user_id")
        log_system_event('INFO', 'upload', f'User uploaded manga: {title} with {page_count} pages in Chapter 1', uploader_id, {'manga_id': manga_id, 'book_type': 'manga', 'chapters': 1, 'pages': page_count})

        flash(f"Manga series created successfully with {page_count} pages in Chapter 1. You can add more chapters anytime.", "success")
        return redirect(url_for("manga"))


# ---------- Edit / Delete Book ----------
@app.route("/book/<int:id>/edit", methods=["GET", "POST"])
@role_required("admin", "publisher")
def edit_book(id):
    try:
        if "user_id" not in session:
            return redirect(url_for("login"))

        conn = get_conn()
        c = conn.cursor()

        # pull everything we need, including description and uploader
        c.execute("""
            SELECT id, title, author, category, description,
                   pdf_filename, audio_filename, cover_path, uploader_id, book_type
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
            "description": row[4],
            "pdf_filename": row[5],
            "audio_filename": row[6],
            "cover_path": row[7],
            "uploader_id": row[8],
            "book_type": row[9],
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

            # support multiple categories (checkboxes named 'categories')
            categories_list = request.form.getlist('categories')
            if categories_list:
                category = ",".join([c.strip() for c in categories_list if c.strip()])
            else:
                category = (request.form.get("category") or "").strip()

            description = (request.form.get('description') or '').strip()

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
                       description = ?,
                       pdf_filename = ?,
                       audio_filename = ?,
                       cover_path = ?
                 WHERE id = ?
            """, (title, author, category, description, pdf_filename, audio_filename, cover_path, id))

            conn.commit()
            conn.close()
            flash("Book updated successfully.", "success")
            return redirect(url_for("view_book", id=id))

        # GET: show the form
        # prepare category list for template (avoid depending on Jinja split filter)
        selected_categories = []
        if book.get('category'):
            selected_categories = [c.strip() for c in book['category'].split(',') if c.strip()]
        conn.close()
        return render_template("edit_book.html", book=book, selected_categories=selected_categories)

    except Exception as e:
        import traceback
        traceback.print_exc()
        try:
            conn.close()
        except Exception:
            pass
        flash(f"Error loading edit page: {str(e)}", "danger")
        return redirect(url_for('home'))


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
@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()

        # --- avatar upload (optional) ---
        avatar = request.files.get("avatar")
        avatar_url = None

        if avatar and avatar.filename:
            from werkzeug.utils import secure_filename
            import os

            UPLOAD_FOLDER = os.path.join("static", "uploads", "avatars")
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)

            ext = avatar.filename.rsplit(".", 1)[-1].lower()
            if ext not in {"png", "jpg", "jpeg", "webp"}:
                flash("Invalid image type. Use PNG/JPG/JPEG/WEBP.", "danger")
                return redirect(url_for("profile"))

            stored_name = f"user_{user_id}.{ext}"
            save_path = os.path.join(UPLOAD_FOLDER, secure_filename(stored_name))
            avatar.save(save_path)
            avatar_url = f"/static/uploads/avatars/{stored_name}"

        conn = get_conn()
        c = conn.cursor()

        # update username/email if provided
        if username:
            c.execute("UPDATE users SET username=? WHERE id=?", (username, user_id))
            session["username"] = username

        if email:
            # only if your users table has email column
            try:
                c.execute("UPDATE users SET email=? WHERE id=?", (email, user_id))
            except Exception:
                pass

        # update avatar_url if uploaded (only if column exists)
        if avatar_url:
            try:
                c.execute("UPDATE users SET avatar_url=? WHERE id=?", (avatar_url, user_id))
                session["avatar_url"] = avatar_url
            except Exception:
                pass

        conn.commit()
        conn.close()

        flash("Profile updated.", "success")
        return redirect(url_for("profile"))
    conn = get_conn()
    c = conn.cursor()

    # Get reading history
    c.execute("""
        SELECT books.title, books.category, history.date_read, books.author, books.cover_path
        FROM history
        JOIN books ON history.book_id = books.id
        WHERE history.user_id = ?
        ORDER BY history.date_read DESC
        LIMIT 50
    """, (user_id,))
    hist = c.fetchall()

    # Get currently reading from watchlist
    c.execute("""
        SELECT b.title, b.author, b.cover_path, w.progress
        FROM watchlist w
        JOIN books b ON w.book_id = b.id
        WHERE w.user_id = ? AND w.status = 'reading'
        ORDER BY w.created_at DESC
        LIMIT 3
    """, (user_id,))
    currently_reading_raw = c.fetchall()

    # Get recent activity from activity log
    c.execute("""
        SELECT al.activity_type, b.title, al.timestamp
        FROM activity_log al
        JOIN books b ON al.book_id = b.id
        WHERE al.user_id = ?
        ORDER BY al.timestamp DESC
        LIMIT 7
    """, (user_id,))
    activity_raw = c.fetchall()

    # Calculate average rating given by user
    c.execute("""
        SELECT AVG(rating) FROM reviews WHERE user_id = ?
    """, (user_id,))
    avg_rating_row = c.fetchone()
    avg_rating = round(avg_rating_row[0], 1) if avg_rating_row[0] else None

    conn.close()

    total_read = len(hist)
    fav_genre = "None yet"
    if total_read:
        cats = [row[1] for row in hist if row[1]]
        fav_genre = Counter(cats).most_common(1)[0][0] if cats else "None yet"

    # Format currently reading
    currently_reading = [
        {"title": r[0], "author": r[1], "progress": r[3] or 0, "cover": r[2]}
        for r in currently_reading_raw
    ]

    # Format recent finished (first 6 from history)
    recent_finished = [
        {"title": r[0], "author": r[3], "cover": r[4]}
        for r in hist[:6]
    ]

    # Format recent activity
    activity_icons = {
        'read': 'fa-book-open',
        'started': 'fa-play-circle',
        'completed': 'fa-check-circle',
        'favorited': 'fa-heart',
        'summarized': 'fa-sparkles'
    }

    recent_activity = []
    for activity_type, title, timestamp in activity_raw:
        try:
            dt = datetime.fromisoformat(timestamp)
            now = datetime.utcnow()
            diff = now - dt

            if diff.days > 365:
                when = f"{diff.days // 365}y ago"
            elif diff.days > 30:
                when = f"{diff.days // 30}mo ago"
            elif diff.days > 0:
                when = f"{diff.days}d ago"
            elif diff.seconds > 3600:
                when = f"{diff.seconds // 3600}h ago"
            elif diff.seconds > 60:
                when = f"{diff.seconds // 60}m ago"
            else:
                when = "Just now"
        except:
            when = timestamp

        activity_text = {
            'read': f"Read <strong>{title}</strong>",
            'started': f"Started reading <strong>{title}</strong>",
            'completed': f"Finished reading <strong>{title}</strong>",
            'favorited': f"Added <strong>{title}</strong> to favorites",
            'summarized': f"Generated summary for <strong>{title}</strong>"
        }.get(activity_type, f"Interacted with <strong>{title}</strong>")

        recent_activity.append({
            "icon": activity_icons.get(activity_type, 'fa-circle'),
            "text": activity_text,
            "when": when
        })


    return render_template(
        "profile.html",
        username=session.get("username"),
        avatar_url=session.get("avatar_url"),
        email=session.get("email"),
        count=total_read,
        fav=fav_genre,
        pages_read=None,  # Could be calculated from progress, but leaving as None for now
        avg_rating=avg_rating,
        currently_reading=currently_reading,
        recent_finished=recent_finished,
        recent_activity=recent_activity
    )

# ---------- Public Profile ----------
@app.route("/u/<username>")
def public_profile(username):
    conn = get_conn()
    c = conn.cursor()

    c.execute("SELECT id, username, role, avatar_url, plan FROM users WHERE username=?", (username,))
    user = c.fetchone()

    if not user:
        conn.close()
        flash("User not found.", "error")
        return redirect(url_for("home"))
    
    user_id = user[0]
    
    # Get stats
    c.execute("SELECT COUNT(*) FROM history WHERE user_id=?", (user_id,))
    read_count = c.fetchone()[0]

    c.execute("SELECT status, COUNT(*) FROM watchlist WHERE user_id=? GROUP BY status", (user_id,))
    watchlist_stats = dict(c.fetchall())

    c.execute("SELECT COUNT(*) FROM favorites WHERE user_id=?", (user_id,))
    fav_count = c.fetchone()[0]

    # Recent activity
    c.execute("""
        SELECT al.activity_type, b.title, al.timestamp
        FROM activity_log al
        JOIN books b ON al.book_id = b.id
        WHERE al.user_id = ?
        ORDER BY al.timestamp DESC
        LIMIT 10
    """, (user_id,))
    activity_raw = c.fetchall()
    
    conn.close()

    # Format activity
    activity_icons = {
        'read': 'fa-book-open',
        'started': 'fa-play-circle',
        'completed': 'fa-check-circle',
        'favorited': 'fa-heart',
        'summarized': 'fa-sparkles'
    }

    recent_activity = []
    for activity_type, title, timestamp in activity_raw:
        try:
            dt = datetime.fromisoformat(timestamp)
            now = datetime.utcnow()
            diff = now - dt

            if diff.days > 365:
                when = f"{diff.days // 365}y ago"
            elif diff.days > 30:
                when = f"{diff.days // 30}mo ago"
            elif diff.days > 0:
                when = f"{diff.days}d ago"
            elif diff.seconds > 3600:
                when = f"{diff.seconds // 3600}h ago"
            elif diff.seconds > 60:
                when = f"{diff.seconds // 60}m ago"
            else:
                when = "Just now"
        except:
            when = timestamp
        
        recent_activity.append({
            'type': activity_type.replace('_', ' ').title(),
            'title': title,
            'when': when,
            'icon': activity_icons.get(activity_type, 'fa-circle')
        })

    return render_template(
        "user_profile.html",
        user=user,
        read_count=read_count,
        watchlist_stats=watchlist_stats,
        fav_count=fav_count,
        recent_activity=recent_activity
    )


# ---------- Settings ----------
@app.route("/settings", methods=["GET", "POST"])
def settings():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    if request.method == "POST":
        action = request.form.get("action")

        if action == "change_password":
            current_password = request.form.get("current_password", "").strip()
            new_password = request.form.get("new_password", "").strip()
            confirm_password = request.form.get("confirm_password", "").strip()

            if not current_password or not new_password or not confirm_password:
                flash("All password fields are required.", "danger")
                return redirect(url_for("settings"))

            if new_password != confirm_password:
                flash("New passwords do not match.", "danger")
                return redirect(url_for("settings"))

            if len(new_password) < 3:
                flash("Password must be at least 3 characters.", "danger")
                return redirect(url_for("settings"))

            # Verify current password
            conn = get_conn()
            c = conn.cursor()
            c.execute("SELECT password FROM users WHERE id=?", (user_id,))
            row = c.fetchone()
            conn.close()

            if not row or row[0] != current_password:
                flash("Current password is incorrect.", "danger")
                return redirect(url_for("settings"))

            # Update password
            conn = get_conn()
            c = conn.cursor()
            c.execute("UPDATE users SET password=? WHERE id=?", (new_password, user_id))
            conn.commit()
            conn.close()

            flash("Password changed successfully.", "success")
            return redirect(url_for("settings"))

        elif action == "update_account":
            username = request.form.get("username", "").strip()
            email = request.form.get("email", "").strip()

            if not username:
                flash("Username is required.", "danger")
                return redirect(url_for("settings"))

            conn = get_conn()
            c = conn.cursor()

            # Check if username is taken by another user
            c.execute("SELECT id FROM users WHERE username=? AND id != ?", (username, user_id))
            if c.fetchone():
                conn.close()
                flash("Username is already taken.", "danger")
                return redirect(url_for("settings"))

            # Update username and email
            c.execute("UPDATE users SET username=? WHERE id=?", (username, user_id))
            session["username"] = username

            if email:
                try:
                    c.execute("UPDATE users SET email=? WHERE id=?", (email, user_id))
                    session["email"] = email
                except Exception:
                    pass

            conn.commit()
            conn.close()

            flash("Account settings updated.", "success")
            return redirect(url_for("settings"))

    # GET request - show settings page
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT username, email FROM users WHERE id=?", (user_id,))
    user_data = c.fetchone()
    conn.close()

    return render_template("settings.html", user=user_data)


# ---------- Activity Log ----------
@app.route("/api/activity-log")
def get_activity_log():
    """Get user's activity log for the modal"""
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    user_id = session["user_id"]
    limit = request.args.get("limit", 5, type=int)
    
    conn = get_conn()
    c = conn.cursor()
    
    # Get activity log with book details
    c.execute("""
        SELECT 
            al.id,
            al.activity_type,
            al.summary_generated,
            b.title,
            al.timestamp
        FROM activity_log al
        JOIN books b ON al.book_id = b.id
        WHERE al.user_id = ?
        ORDER BY al.timestamp DESC
        LIMIT ?
    """, (user_id, limit))
    
    activities = []
    for row in c.fetchall():
        activity_id, activity_type, summary_gen, title, timestamp = row
        
        # Format timestamp to relative time
        from datetime import datetime
        try:
            dt = datetime.fromisoformat(timestamp)
            now = datetime.utcnow()
            diff = now - dt
            
            if diff.days > 365:
                when = f"{diff.days // 365} year{'s' if diff.days // 365 > 1 else ''} ago"
            elif diff.days > 30:
                when = f"{diff.days // 30} month{'s' if diff.days // 30 > 1 else ''} ago"
            elif diff.days > 0:
                when = f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
            elif diff.seconds > 3600:
                when = f"{diff.seconds // 3600} hour{'s' if diff.seconds // 3600 > 1 else ''} ago"
            elif diff.seconds > 60:
                when = f"{diff.seconds // 60} minute{'s' if diff.seconds // 60 > 1 else ''} ago"
            else:
                when = "Just now"
        except:
            when = timestamp
        
        activity_icon = {
            'read': 'fa-book-open',
            'started': 'fa-play-circle',
            'completed': 'fa-check-circle',
            'summarized': 'fa-sparkles'
        }.get(activity_type, 'fa-circle')
        
        activities.append({
            'type': activity_type,
            'title': title,
            'when': when,
            'icon': activity_icon,
            'has_summary': summary_gen == 1
        })
    
    conn.close()
    return jsonify(activities)


@app.route("/api/log-activity", methods=["POST"])
def log_activity():
    """Log a user activity"""
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    data = request.get_json()
    user_id = session["user_id"]
    book_id = data.get("book_id")
    activity_type = data.get("type", "read")  # read, started, completed, summarized
    summary_generated = 1 if data.get("has_summary") else 0
    
    conn = get_conn()
    c = conn.cursor()
    
    try:
        c.execute("""
            INSERT INTO activity_log (user_id, book_id, activity_type, summary_generated)
            VALUES (?, ?, ?, ?)
        """, (user_id, book_id, activity_type, summary_generated))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 500


# ---------- Watchlist ----------
@app.route("/watchlist")
def watchlist():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_conn()
    c = conn.cursor()
    
    # Watchlist books
    rows = c.execute("""
        SELECT b.id, b.title, b.author, COALESCE(b.category, 'General'),
               b.pdf_filename, b.audio_filename, b.cover_path,
               w.status, w.progress, w.created_at
        FROM watchlist w
        JOIN books b ON b.id = w.book_id
        WHERE w.user_id = ?
        ORDER BY datetime(w.created_at) DESC
    """, (session["user_id"],)).fetchall()
    
    # Recently read books from history
    recently_read = c.execute("""
        SELECT b.id, b.title, b.author, COALESCE(b.category, 'General'),
               b.pdf_filename, b.audio_filename, b.cover_path,
               h.date_read
        FROM history h
        JOIN books b ON b.id = h.book_id
        WHERE h.user_id = ?
        ORDER BY h.date_read DESC
        LIMIT 20
    """, (session["user_id"],)).fetchall()
    
    # Get unique categories from watchlist
    categories = sorted(set([row[3] for row in rows]))
    
    conn.close()

    # Group featured books by status
    featured_books = {}
    for status in ['planned', 'reading', 'on_hold', 'completed', 'dropped']:
        featured_books[status] = [
            {"id": r[0], "title": r[1], "author": r[2], "category": r[3], "progress": r[8] or 0, "cover": r[6], "status": r[7]}
            for r in rows if r[7] == status
        ][:3]  # First 3 for each status

    table_books = [
        {"id": r[0], "title": r[1], "author": r[2], "category": r[3], "year": "", "rating": 4, "cover": r[6], "status": r[7], "progress": r[8]}
        for r in rows
    ]
    
    recently_read_books = [
        {"id": r[0], "title": r[1], "author": r[2], "category": r[3], "cover": r[6], "date_read": r[7]}
        for r in recently_read
    ]
    
    return render_template("watchlist.html", featured_books=featured_books, table_books=table_books, categories=categories, recently_read_books=recently_read_books)


@app.post("/watchlist/add")
def watchlist_add():
    if "user_id" not in session:
        return redirect(url_for("login"))
    book_id = request.form.get("book_id", "").strip()
    if not book_id.isdigit():
        # Prevent browser back button from showing login page after successful login
        response = redirect(url_for("home"))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
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

    # Check if already in watchlist
    c.execute("SELECT id FROM watchlist WHERE user_id=? AND book_id=?", (session["user_id"], book_id))
    existing = c.fetchone()

    if existing:
        # Update existing
        c.execute("UPDATE watchlist SET status=?, progress=? WHERE user_id=? AND book_id=?",
                  (status, progress, session["user_id"], book_id))
    else:
        # Insert new
        c.execute("INSERT INTO watchlist (user_id, book_id, status, progress) VALUES (?, ?, ?, ?)",
                  (session["user_id"], book_id, status, progress))

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

        # Log activity if marked as completed
        if status.lower() == 'completed':
            try:
                c.execute("""
                    INSERT INTO activity_log (user_id, book_id, activity_type)
                    VALUES (?, ?, ?)
                """, (user_id, book_id, 'completed'))
                conn.commit()
            except Exception:
                pass

    conn.commit()
    conn.close()
    return redirect(url_for("view_book", id=book_id))


# ---------- Favorites ----------
@app.route("/favorites")
def favorites():
    """Display user's favorite books"""
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_conn()
    c = conn.cursor()
    
    # Get favorite books with details
    favorite_books = c.execute("""
        SELECT b.id, b.title, b.author, COALESCE(b.category, 'General') AS category,
               b.pdf_filename, b.audio_filename, b.cover_path,
               f.created_at
        FROM favorites f
        JOIN books b ON b.id = f.book_id
        WHERE f.user_id = ?
        ORDER BY datetime(f.created_at) DESC
    """, (session["user_id"],)).fetchall()
    
    # Get unique categories from favorites
    categories = sorted(set([row[3] for row in favorite_books]))
    
    # Get recently read books from history
    recently_read = c.execute("""
        SELECT b.id, b.title, b.author, COALESCE(b.category, 'General'),
               b.pdf_filename, b.audio_filename, b.cover_path,
               h.date_read
        FROM history h
        JOIN books b ON b.id = h.book_id
        WHERE h.user_id = ?
        ORDER BY h.date_read DESC
        LIMIT 20
    """, (session["user_id"],)).fetchall()
    
    conn.close()

    # Format data for template
    favorite_books_formatted = [
        {
            "id": r[0], 
            "title": r[1], 
            "author": r[2], 
            "category": r[3], 
            "cover": r[6],
            "date_added": r[7]
        }
        for r in favorite_books
    ]
    
    recently_read_books = [
        {"id": r[0], "title": r[1], "author": r[2], "category": r[3], "cover": r[6], "date_read": r[7]}
        for r in recently_read
    ]
    
    return render_template("favorites.html", 
                         favorite_books=favorite_books_formatted, 
                         categories=categories,
                         recently_read_books=recently_read_books)


@app.post("/favorites/add")
def favorites_add():
    """Add a book to favorites"""
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    book_id = request.form.get("book_id", "").strip()
    if not book_id.isdigit():
        flash("Invalid book ID.", "danger")
        return redirect(url_for("home"))
    
    conn = get_conn()
    c = conn.cursor()
    
    # Verify book exists
    c.execute("SELECT 1 FROM books WHERE id=?", (book_id,))
    if not c.fetchone():
        conn.close()
        flash("Book not found.", "danger")
        return redirect(url_for("home"))
    
    # Check if already in favorites
    c.execute("SELECT 1 FROM favorites WHERE user_id=? AND book_id=?", (session["user_id"], book_id))
    if c.fetchone():
        conn.close()
        flash("Book is already in your favorites.", "info")
        return redirect(request.referrer or url_for("home"))
    
    # Add to favorites
    try:
        c.execute("INSERT INTO favorites (user_id, book_id) VALUES (?, ?)", (session["user_id"], book_id))
        conn.commit()
        
        # Log activity
        try:
            c.execute("""
                INSERT INTO activity_log (user_id, book_id, activity_type)
                VALUES (?, ?, ?)
            """, (session["user_id"], book_id, 'favorited'))
            conn.commit()
        except Exception:
            pass
            
        conn.close()
        flash("Book added to favorites!", "success")
    except Exception as e:
        conn.close()
        flash("Error adding to favorites.", "danger")
    
    return redirect(request.referrer or url_for("home"))


@app.post("/favorites/remove")
def favorites_remove():
    """Remove a book from favorites"""
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    book_id = request.form.get("book_id", "").strip()
    if not book_id.isdigit():
        flash("Invalid book ID.", "danger")
        return redirect(url_for("favorites"))
    
    conn = get_conn()
    c = conn.cursor()
    
    # Remove from favorites
    c.execute("DELETE FROM favorites WHERE user_id=? AND book_id=?", (session["user_id"], book_id))
    
    conn.commit()
    conn.close()
    
    flash("Book removed from favorites.", "success")
    return redirect(url_for("favorites"))


@app.post("/favorites/book/<int:book_id>")
def favorites_book(book_id):
    """Toggle favorite status for a book from the book detail page"""
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_conn()
    c = conn.cursor()

    # make sure the book exists
    c.execute("SELECT 1 FROM books WHERE id=?", (book_id,))
    if not c.fetchone():
        conn.close()
        flash("Book not found.", "danger")
        return redirect(url_for("home"))

    user_id = session["user_id"]

    # Check if already in favorites
    c.execute("SELECT 1 FROM favorites WHERE user_id=? AND book_id=?", (user_id, book_id))
    if c.fetchone():
        # Remove from favorites
        c.execute("DELETE FROM favorites WHERE user_id=? AND book_id=?", (user_id, book_id))
        conn.commit()
        conn.close()
        flash("Removed from favorites.", "info")
    else:
        # Add to favorites
        c.execute("INSERT INTO favorites (user_id, book_id) VALUES (?, ?)", (user_id, book_id))
        conn.commit()
        
        # Log activity
        try:
            c.execute("""
                INSERT INTO activity_log (user_id, book_id, activity_type)
                VALUES (?, ?, ?)
            """, (user_id, book_id, 'favorited'))
            conn.commit()
        except Exception:
            pass
        
        conn.close()
        flash("Added to favorites!", "success")

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
        SELECT id, title, author, category, pdf_filename, cover_path, description, book_type
        FROM books
        WHERE id = ? AND COALESCE(book_type, 'book') = 'manga'
    """, (id,))
    manga = c.fetchone()

    if not manga:
        conn.close()
        flash("Manga not found.", "danger")
        return redirect(url_for("manga"))

    # Get chapters for this manga
    c.execute("""
        SELECT id, chapter_num, title, pdf_filename, created_at, page_count
        FROM chapters
        WHERE manga_id = ?
        ORDER BY chapter_num ASC
    """, (id,))
    chapters = c.fetchall()

    # Get all manga for series list
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
        "manga_reader_new.html",
        manga=manga,
        chapters=chapters,
        related_manga=related_manga,
        chapter=chapters[0] if chapters else None
    )


# ---------- Modern Manga Reader (v2) ----------
@app.route("/manga/<int:id>")
def manga_reader_v2(id):
    """Modern manga reader with AI features."""
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_conn()
    c = conn.cursor()

    # Fetch manga details
    c.execute("""
        SELECT id, title, author, category, pdf_filename, cover_path, description, book_type
        FROM books
        WHERE id = ? AND COALESCE(book_type, 'book') = 'manga'
    """, (id,))
    manga = c.fetchone()

    if not manga:
        conn.close()
        flash("Manga not found.", "danger")
        return redirect(url_for("manga"))

    # Get chapters for this manga
    c.execute("""
        SELECT id, chapter_num, title, pdf_filename, created_at, page_count
        FROM chapters
        WHERE manga_id = ?
        ORDER BY chapter_num ASC
    """, (id,))
    chapters = c.fetchall()

    conn.close()

    return render_template(
        "manga_reader_new.html",
        manga=manga,
        chapters=chapters,
        chapter=chapters[0] if chapters else None
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
    chapter_format = (request.form.get("chapter_format") or "images").lower().strip()

    if not chapter_num:
        flash("Chapter number is required.", "danger")
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

    page_count = 0
    pages_data = None

    if chapter_format == "pdf":
        # Handle PDF upload - extract pages as images
        chapter_pdf = request.files.get("chapter_pdf")
        if not chapter_pdf or not chapter_pdf.filename:
            conn.close()
            flash("PDF file is required.", "danger")
            return redirect(url_for("upload_chapter", manga_id=manga_id))
        
        ext = chapter_pdf.filename.rsplit(".", 1)[-1].lower()
        if ext not in ALLOWED_PDF:
            conn.close()
            flash("Only PDF files are allowed.", "danger")
            return redirect(url_for("upload_chapter", manga_id=manga_id))
        
        # Save PDF temporarily
        pdf_filename = secure_filename(chapter_pdf.filename)
        pdf_path = os.path.join(UPLOAD_FOLDER_PDF, pdf_filename)
        chapter_pdf.save(pdf_path)
        
        # Create chapter directory for images
        chapter_dir = os.path.join(UPLOAD_FOLDER_MANGA, f"manga_{manga_id}_ch{chapter_num}")
        os.makedirs(chapter_dir, exist_ok=True)
        
        # Try to extract PDF pages as images
        if PDF_EXTRACTION_AVAILABLE:
            try:
                from PIL import Image
                images = convert_from_path(pdf_path, dpi=150)
                page_count = len(images)
                
                for idx, img in enumerate(images, 1):
                    page_filename = f"page_{idx:03d}.png"
                    img_path = os.path.join(chapter_dir, page_filename)
                    img.save(img_path, 'PNG')
                
                pages_data = ",".join([f"page_{i:03d}.png" for i in range(1, page_count + 1)])
                flash(f"PDF extracted successfully! {page_count} pages found.", "info")
            except Exception as e:
                # Fallback: store PDF filename if extraction fails
                # Copy PDF to chapter directory so it can be displayed
                import shutil
                pdf_dest = os.path.join(chapter_dir, pdf_filename)
                shutil.copy(pdf_path, pdf_dest)
                pages_data = pdf_filename
                page_count = 1
                flash(f"PDF uploaded (extraction failed, will display PDF in reader): {str(e)}", "warning")
        else:
            # If pdf2image not available, copy PDF to chapter directory
            import shutil
            pdf_dest = os.path.join(chapter_dir, pdf_filename)
            shutil.copy(pdf_path, pdf_dest)
            pages_data = pdf_filename
            page_count = 1
            flash("PDF uploaded (install pdf2image for page extraction: pip install pdf2image). PDF will display in reader.", "info")
    else:
        # Handle image uploads (multiple pages)
        chapter_pages = request.files.getlist("chapter_pages")
        
        if not chapter_pages or len(chapter_pages) == 0:
            conn.close()
            flash("At least one image file is required.", "danger")
            return redirect(url_for("upload_chapter", manga_id=manga_id))

        # Save chapter pages
        chapter_dir = os.path.join(UPLOAD_FOLDER_MANGA, f"manga_{manga_id}_ch{chapter_num}")
        os.makedirs(chapter_dir, exist_ok=True)
        
        page_files = []
        
        for idx, page_file in enumerate(chapter_pages, 1):
            if page_file and page_file.filename:
                ext = page_file.filename.rsplit(".", 1)[-1].lower()
                if ext in ALLOWED_IMG:
                    # Save with page number for ordering
                    page_filename = f"page_{idx:03d}.{ext}"
                    page_file.save(os.path.join(chapter_dir, page_filename))
                    page_files.append(page_filename)
                    page_count += 1
        
        if page_count == 0:
            conn.close()
            flash("No valid image files were uploaded.", "danger")
            return redirect(url_for("upload_chapter", manga_id=manga_id))

        # Store page files info (comma-separated)
        pages_data = ",".join(page_files)

    # Insert chapter into database
    c.execute("""
        INSERT INTO chapters (manga_id, chapter_num, title, pdf_filename, page_count)
        VALUES (?, ?, ?, ?, ?)
    """, (manga_id, chapter_num, chapter_title, pages_data, page_count))
    conn.commit()
    conn.close()

    format_label = "PDF" if chapter_format == "pdf" else f"{page_count} pages"
    flash(f"Chapter {chapter_num} uploaded successfully ({format_label})!", "success")
    return redirect(url_for("upload_chapter", manga_id=manga_id))


# ---------- Edit Chapter ----------
@app.route("/manga/<int:manga_id>/chapter/<int:chapter_num>/edit", methods=["GET", "POST"])
def edit_chapter(manga_id, chapter_num):
    if request.method == "GET":
        # Show edit form
        conn = get_conn()
        c = conn.cursor()
        
        # Get manga info
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

        # Get chapter info
        c.execute("""
            SELECT id, chapter_num, title, pdf_filename, page_count
            FROM chapters
            WHERE manga_id = ? AND chapter_num = ?
        """, (manga_id, chapter_num))
        chapter = c.fetchone()

        if not chapter:
            conn.close()
            flash("Chapter not found.", "danger")
            return redirect(url_for("upload_chapter", manga_id=manga_id))

        conn.close()

        return render_template("edit_chapter.html", 
                             manga=manga,
                             chapter_id=chapter[0],
                             chapter_num=chapter[1],
                             chapter_title=chapter[2],
                             page_count=chapter[4])

    # POST - update chapter
    chapter_title = request.form.get("chapter_title", "").strip()
    chapter_format = (request.form.get("chapter_format") or "images").lower().strip()

    # Get current chapter info
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT id, title, pdf_filename
        FROM chapters
        WHERE manga_id = ? AND chapter_num = ?
    """, (manga_id, chapter_num))
    chapter = c.fetchone()

    if not chapter:
        conn.close()
        flash("Chapter not found.", "danger")
        return redirect(url_for("upload_chapter", manga_id=manga_id))

    chapter_id = chapter[0]
    current_title = chapter[1]
    
    # Update title if provided
    if chapter_title:
        c.execute("""
            UPDATE chapters
            SET title = ?
            WHERE id = ?
        """, (chapter_title, chapter_id))
    
    page_count = 0
    pages_data = None

    # Handle file uploads
    if chapter_format == "pdf":
        chapter_pdf = request.files.get("chapter_pdf")
        if not chapter_pdf or not chapter_pdf.filename:
            conn.commit()
            conn.close()
            flash("No files selected. Chapter title updated.", "info")
            return redirect(url_for("upload_chapter", manga_id=manga_id))
        
        ext = chapter_pdf.filename.rsplit(".", 1)[-1].lower()
        if ext not in ALLOWED_PDF:
            conn.close()
            flash("Only PDF files are allowed.", "danger")
            return redirect(url_for("edit_chapter", manga_id=manga_id, chapter_num=chapter_num))
        
        # Save PDF temporarily
        pdf_filename = secure_filename(chapter_pdf.filename)
        pdf_path = os.path.join(UPLOAD_FOLDER_PDF, pdf_filename)
        chapter_pdf.save(pdf_path)
        
        # Create/clear chapter directory for images
        chapter_dir = os.path.join(UPLOAD_FOLDER_MANGA, f"manga_{manga_id}_ch{chapter_num}")
        if os.path.exists(chapter_dir):
            import shutil
            shutil.rmtree(chapter_dir)
        os.makedirs(chapter_dir, exist_ok=True)
        
        # Try to extract PDF pages as images
        if PDF_EXTRACTION_AVAILABLE:
            try:
                from PIL import Image
                images = convert_from_path(pdf_path, dpi=150)
                page_count = len(images)
                
                for idx, img in enumerate(images, 1):
                    page_filename = f"page_{idx:03d}.png"
                    img_path = os.path.join(chapter_dir, page_filename)
                    img.save(img_path, 'PNG')
                
                pages_data = ",".join([f"page_{i:03d}.png" for i in range(1, page_count + 1)])
                flash(f"PDF extracted successfully! {page_count} pages found.", "info")
            except Exception as e:
                # Fallback: copy PDF to chapter directory
                import shutil
                pdf_dest = os.path.join(chapter_dir, pdf_filename)
                shutil.copy(pdf_path, pdf_dest)
                pages_data = pdf_filename
                page_count = 1
                flash(f"PDF uploaded (extraction failed, will display PDF in reader): {str(e)}", "warning")
        else:
            # Copy PDF to chapter directory if extraction not available
            import shutil
            pdf_dest = os.path.join(chapter_dir, pdf_filename)
            shutil.copy(pdf_path, pdf_dest)
            pages_data = pdf_filename
            page_count = 1
            flash("PDF uploaded (install pdf2image for page extraction). PDF will display in reader.", "info")
        
        # Update chapter with new data
        c.execute("""
            UPDATE chapters
            SET pdf_filename = ?, page_count = ?
            WHERE id = ?
        """, (pages_data, page_count, chapter_id))
    
    else:
        # Handle image uploads
        chapter_pages = request.files.getlist("chapter_pages")
        
        if not chapter_pages or len(chapter_pages) == 0:
            conn.commit()
            conn.close()
            flash("No files selected. Chapter title updated.", "info")
            return redirect(url_for("upload_chapter", manga_id=manga_id))

        # Clear chapter directory
        chapter_dir = os.path.join(UPLOAD_FOLDER_MANGA, f"manga_{manga_id}_ch{chapter_num}")
        if os.path.exists(chapter_dir):
            import shutil
            shutil.rmtree(chapter_dir)
        os.makedirs(chapter_dir, exist_ok=True)
        
        page_files = []
        
        for idx, page_file in enumerate(chapter_pages, 1):
            if page_file and page_file.filename:
                ext = page_file.filename.rsplit(".", 1)[-1].lower()
                if ext in ALLOWED_IMG:
                    page_filename = f"page_{idx:03d}.{ext}"
                    page_file.save(os.path.join(chapter_dir, page_filename))
                    page_files.append(page_filename)
                    page_count += 1
        
        if page_count == 0:
            conn.close()
            flash("No valid image files were uploaded.", "danger")
            return redirect(url_for("edit_chapter", manga_id=manga_id, chapter_num=chapter_num))

        pages_data = ",".join(page_files)
        
        # Update chapter with new data
        c.execute("""
            UPDATE chapters
            SET pdf_filename = ?, page_count = ?
            WHERE id = ?
        """, (pages_data, page_count, chapter_id))
    
    conn.commit()
    conn.close()

    format_label = "PDF" if chapter_format == "pdf" else f"{page_count} pages"
    flash(f"Chapter {chapter_num} updated successfully ({format_label})!", "success")
    return redirect(url_for("upload_chapter", manga_id=manga_id))


# ---------- Delete Chapter (by number) ----------
@app.route("/manga/<int:manga_id>/chapter/<int:chapter_num>/delete", methods=["GET"])
def delete_chapter_by_num(manga_id, chapter_num):
    conn = get_conn()
    c = conn.cursor()
    
    # Get chapter info
    c.execute("""
        SELECT id
        FROM chapters
        WHERE manga_id = ? AND chapter_num = ?
    """, (manga_id, chapter_num))
    chapter = c.fetchone()

    if not chapter:
        conn.close()
        flash("Chapter not found.", "danger")
        return redirect(url_for("upload_chapter", manga_id=manga_id))

    chapter_id = chapter[0]
    
    # Delete chapter directory
    chapter_dir = os.path.join(UPLOAD_FOLDER_MANGA, f"manga_{manga_id}_ch{chapter_num}")
    if os.path.exists(chapter_dir):
        import shutil
        shutil.rmtree(chapter_dir)
    
    # Delete from database
    c.execute("DELETE FROM chapters WHERE id = ?", (chapter_id,))
    conn.commit()
    conn.close()

    flash(f"Chapter {chapter_num} deleted successfully!", "success")
    return redirect(url_for("upload_chapter", manga_id=manga_id))


# ---------- View Chapter ----------
@app.route("/manga/<int:manga_id>/chapter/<int:chapter_id>")
def view_chapter(manga_id, chapter_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_conn()
    c = conn.cursor()

    # Fetch manga details
    c.execute("""
        SELECT id, title, author, category, cover_path, description
        FROM books
        WHERE id = ? AND COALESCE(book_type, 'book') = 'manga'
    """, (manga_id,))
    manga = c.fetchone()

    if not manga:
        conn.close()
        flash("Manga not found.", "danger")
        return redirect(url_for("manga"))

    # Fetch chapter details
    c.execute("""
        SELECT id, chapter_num, title, pdf_filename, page_count, created_at
        FROM chapters
        WHERE id = ? AND manga_id = ?
    """, (chapter_id, manga_id))
    chapter = c.fetchone()

    if not chapter:
        conn.close()
        flash("Chapter not found.", "danger")
        return redirect(url_for("read_manga", id=manga_id))

    # Get all chapters for navigation
    c.execute("""
        SELECT id, chapter_num, title
        FROM chapters
        WHERE manga_id = ?
        ORDER BY chapter_num ASC
    """, (manga_id,))
    chapters = c.fetchall()

    conn.close()

    return render_template(
        "chapter_viewer.html",
        manga=manga,
        chapter=chapter,
        chapters=chapters
    )


# API endpoint to fetch chapter pages
@app.route('/api/chapter/<int:chapter_id>/pages', methods=['GET'])
def get_chapter_pages(chapter_id):
    """Fetch list of pages for a chapter."""
    if 'user_id' not in session:
        return jsonify({'error': 'login required'}), 401
    
    conn = get_conn()
    c = conn.cursor()
    
    # Get chapter info
    c.execute("""
        SELECT id, manga_id, chapter_num, pdf_filename, page_count
        FROM chapters
        WHERE id = ?
    """, (chapter_id,))
    chapter = c.fetchone()
    conn.close()
    
    if not chapter:
        return jsonify({'error': 'chapter not found'}), 404
    
    chapter_id, manga_id, chapter_num, pdf_filename, page_count = chapter
    
    # Get list of image files in chapter directory
    chapter_dir = os.path.join(UPLOAD_FOLDER_MANGA, f"manga_{manga_id}_ch{chapter_num}")
    pages = []
    
    if os.path.exists(chapter_dir):
        # Get all image files
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
        files = sorted([f for f in os.listdir(chapter_dir) 
                       if os.path.splitext(f)[1].lower() in image_extensions],
                      key=lambda x: int(''.join(filter(str.isdigit, x)) or '0'))
        
        for idx, filename in enumerate(files, 1):
            pages.append({
                'page_num': idx,
                'url': f'/static/manga/manga_{manga_id}_ch{chapter_num}/{filename}'
            })
    
    return jsonify(pages)


# API endpoint to get chapters for a manga
@app.route('/api/manga/<int:manga_id>/chapters', methods=['GET'])
def get_manga_chapters(manga_id):
    """Get all chapters for a manga."""
    if 'user_id' not in session:
        return jsonify({'error': 'login required'}), 401
    
    conn = get_conn()
    c = conn.cursor()
    
    # Get chapters
    c.execute("""
        SELECT id, chapter_num, title, page_count
        FROM chapters
        WHERE manga_id = ?
        ORDER BY chapter_num ASC
    """, (manga_id,))
    chapters = c.fetchall()
    conn.close()
    
    return jsonify([{
        'id': ch[0],
        'chapter_num': ch[1],
        'title': ch[2],
        'page_count': ch[3]
    } for ch in chapters])


# API endpoint to update chapter
@app.route('/api/chapter/<int:chapter_id>', methods=['PUT'])
def update_chapter(chapter_id):
    """Update chapter title."""
    if 'user_id' not in session:
        return jsonify({'error': 'login required'}), 401
    
    data = request.get_json(silent=True) or {}
    title = (data.get('title') or '').strip()
    
    if not title:
        return jsonify({'error': 'title required'}), 400
    
    conn = get_conn()
    c = conn.cursor()
    
    # Get chapter and verify permissions
    c.execute("SELECT manga_id FROM chapters WHERE id = ?", (chapter_id,))
    chapter = c.fetchone()
    if not chapter:
        conn.close()
        return jsonify({'error': 'chapter not found'}), 404
    
    manga_id = chapter[0]
    c.execute("SELECT author FROM books WHERE id = ?", (manga_id,))
    manga = c.fetchone()
    
    user_id = session.get('user_id')
    c.execute("SELECT role FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    
    # Only admin, publisher, or manga author can edit chapters
    if user[0] not in ('admin', 'publisher') and manga[0] != user_id:
        conn.close()
        return jsonify({'error': 'permission denied'}), 403
    
    try:
        c.execute("UPDATE chapters SET title = ? WHERE id = ?", (title, chapter_id))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 400


# API endpoint to delete chapter
@app.route('/api/chapter/<int:chapter_id>', methods=['DELETE'])
def delete_chapter(chapter_id):
    """Delete a chapter."""
    if 'user_id' not in session:
        return jsonify({'error': 'login required'}), 401
    
    conn = get_conn()
    c = conn.cursor()
    
    # Get chapter and verify permissions
    c.execute("SELECT manga_id, chapter_num FROM chapters WHERE id = ?", (chapter_id,))
    chapter = c.fetchone()
    if not chapter:
        conn.close()
        return jsonify({'error': 'chapter not found'}), 404
    
    manga_id, chapter_num = chapter
    c.execute("SELECT author FROM books WHERE id = ?", (manga_id,))
    manga = c.fetchone()
    
    user_id = session.get('user_id')
    c.execute("SELECT role FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    
    # Only admin, publisher, or manga author can delete chapters
    if user[0] not in ('admin', 'publisher') and manga[0] != user_id:
        conn.close()
        return jsonify({'error': 'permission denied'}), 403
    
    try:
        # Delete chapter from database
        c.execute("DELETE FROM chapters WHERE id = ?", (chapter_id,))
        conn.commit()
        conn.close()
        
        # Optionally delete chapter files
        import shutil
        chapter_dir = os.path.join(UPLOAD_FOLDER_MANGA, f"manga_{manga_id}_ch{chapter_num}")
        if os.path.exists(chapter_dir):
            try:
                shutil.rmtree(chapter_dir)
            except Exception as e:
                print(f"Warning: Could not delete chapter directory: {e}")
        
        return jsonify({'success': True})
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 400


@app.route('/report_manga', methods=['POST'])
def report_manga():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'login required'}), 401

    data = request.get_json(silent=True) or request.form or {}
    try:
        manga_id = int(data.get('manga_id'))
    except Exception:
        return jsonify({'success': False, 'error': 'invalid manga id'}), 400

    reason = (data.get('reason') or '').strip()[:1000]

    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO reports (user_id, manga_id, reason)
        VALUES (?, ?, ?)
    """, (session.get('user_id'), manga_id, reason))
    conn.commit()
    conn.close()

    return jsonify({'success': True})


@app.route('/report_user', methods=['POST'])
def report_user():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'login required'}), 401

    data = request.get_json(silent=True) or request.form or {}
    try:
        reported_user_id = int(data.get('reported_user_id'))
    except Exception:
        return jsonify({'success': False, 'error': 'invalid user id'}), 400

    reason = (data.get('reason') or 'Inappropriate behavior').strip()[:1000]

    # Store the report in database
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO user_reports (reporter_id, reported_user_id, reason)
        VALUES (?, ?, ?)
    """, (session.get('user_id'), reported_user_id, reason))
    conn.commit()
    conn.close()

    # Log the user report
    log_system_event('WARNING', 'user_report', f'User {session.get("username")} reported user ID {reported_user_id}', session.get('user_id'), {'reported_user_id': reported_user_id, 'reason': reason})

    return jsonify({'success': True})


@app.route('/user/<int:user_id>')
def user_profile(user_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Don't allow users to view their own profile through this route
    if user_id == session.get('user_id'):
        return redirect(url_for('profile'))

    conn = get_conn()
    c = conn.cursor()

    # Get user info
    c.execute("""
        SELECT id, username, email, role, avatar_url, plan
        FROM users
        WHERE id = ?
    """, (user_id,))

    user = c.fetchone()
    if not user:
        conn.close()
        flash('User not found.', 'danger')
        return redirect(url_for('home'))

    # Get user's uploaded books
    c.execute("""
        SELECT id, title, author, category, cover_path, created_at
        FROM books
        WHERE uploader_id = ? AND book_type != 'manga'
        ORDER BY created_at DESC
        LIMIT 10
    """, (user_id,))

    books = c.fetchall()

    # Get user's reading activity
    c.execute("""
        SELECT COUNT(*) FROM activity_log WHERE user_id = ?
    """, (user_id,))

    activity_count = c.fetchone()[0]

    # Get user's review count
    c.execute("""
        SELECT COUNT(*) FROM reviews WHERE user_id = ?
    """, (user_id,))

    review_count = c.fetchone()[0]

    conn.close()

    return render_template('user_profile.html',
                         user=user,
                         books=books,
                         activity_count=activity_count,
                         review_count=review_count)


# ---------- Manga Character Management ----------
@app.route('/api/manga/<int:manga_id>/characters', methods=['GET'])
def get_manga_characters(manga_id):
    """Get all characters for a manga."""
    if 'user_id' not in session:
        return jsonify({'error': 'login required'}), 401
    
    conn = get_conn()
    c = conn.cursor()
    
    # Verify manga exists
    c.execute("SELECT id FROM books WHERE id = ? AND COALESCE(book_type, 'book') = 'manga'", (manga_id,))
    if not c.fetchone():
        conn.close()
        return jsonify({'error': 'manga not found'}), 404
    
    # Get characters
    c.execute("""
        SELECT id, name, description, role, avatar_url
        FROM manga_characters
        WHERE manga_id = ?
        ORDER BY id ASC
    """, (manga_id,))
    characters = c.fetchall()
    conn.close()
    
    return jsonify([{
        'id': ch[0],
        'name': ch[1],
        'description': ch[2],
        'role': ch[3],
        'avatar_url': ch[4]
    } for ch in characters])


@app.route('/api/manga/<int:manga_id>/characters', methods=['POST'])
def add_manga_character(manga_id):
    """Add a new character to a manga."""
    if 'user_id' not in session:
        return jsonify({'error': 'login required'}), 401
    
    name = (request.form.get('name') or '').strip()
    description = (request.form.get('description') or '').strip()
    role = (request.form.get('role') or '').strip()
    avatar_file = request.files.get('avatar')
    
    if not name:
        return jsonify({'error': 'character name required'}), 400
    
    conn = get_conn()
    c = conn.cursor()
    
    # Verify manga exists and user can edit it
    c.execute("SELECT id, uploader_id FROM books WHERE id = ? AND COALESCE(book_type, 'book') = 'manga'", (manga_id,))
    manga = c.fetchone()
    if not manga:
        conn.close()
        return jsonify({'error': 'manga not found'}), 404
    
    user_id = session.get('user_id')
    c.execute("SELECT role FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    
    # Only admin, publisher, or manga author can add characters
    if user[0] not in ('admin', 'publisher') and manga[1] != session.get('user_id'):
        conn.close()
        return jsonify({'error': 'permission denied'}), 403
    
    avatar_url = None
    
    # Handle avatar upload
    if avatar_file and avatar_file.filename:
        ext = avatar_file.filename.rsplit(".", 1)[-1].lower()
        if ext in ALLOWED_IMG:
            fname = secure_filename(f"char_{manga_id}_{int(datetime.now().timestamp())}.{ext}")
            avatar_file.save(os.path.join(UPLOAD_FOLDER_COVERS, fname))
            avatar_url = f"/static/covers/{fname}"
    
    try:
        c.execute("""
            INSERT INTO manga_characters (manga_id, name, description, role, avatar_url)
            VALUES (?, ?, ?, ?, ?)
        """, (manga_id, name, description, role, avatar_url))
        conn.commit()
        
        char_id = c.lastrowid
        conn.close()
        
        return jsonify({
            'success': True,
            'id': char_id,
            'name': name,
            'description': description,
            'role': role,
            'avatar_url': avatar_url
        }), 201
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 400


@app.route('/api/manga/character/<int:character_id>', methods=['PUT'])
def update_manga_character(character_id):
    """Update a manga character."""
    if 'user_id' not in session:
        return jsonify({'error': 'login required'}), 401
    
    name = (request.form.get('name') or '').strip()
    description = (request.form.get('description') or '').strip()
    role = (request.form.get('role') or '').strip()
    avatar_file = request.files.get('avatar')
    
    if not name:
        return jsonify({'error': 'character name required'}), 400
    
    conn = get_conn()
    c = conn.cursor()
    
    # Get character and verify permissions
    c.execute("SELECT manga_id, avatar_url FROM manga_characters WHERE id = ?", (character_id,))
    char = c.fetchone()
    if not char:
        conn.close()
        return jsonify({'error': 'character not found'}), 404
    
    manga_id = char[0]
    current_avatar = char[1]
    
    c.execute("SELECT uploader_id FROM books WHERE id = ?", (manga_id,))
    manga = c.fetchone()
    
    user_id = session.get('user_id')
    c.execute("SELECT role FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    
    if user[0] not in ('admin', 'publisher') and manga[0] != user_id:
        conn.close()
        return jsonify({'error': 'permission denied'}), 403
    
    avatar_url = current_avatar
    
    # Handle avatar upload
    if avatar_file and avatar_file.filename:
        ext = avatar_file.filename.rsplit(".", 1)[-1].lower()
        if ext in ALLOWED_IMG:
            fname = secure_filename(f"char_{character_id}_{int(datetime.now().timestamp())}.{ext}")
            avatar_file.save(os.path.join(UPLOAD_FOLDER_COVERS, fname))
            avatar_url = f"/static/covers/{fname}"
    
    try:
        c.execute("""
            UPDATE manga_characters
            SET name = ?, description = ?, role = ?, avatar_url = ?
            WHERE id = ?
        """, (name, description, role, avatar_url or None, character_id))
        conn.commit()
        
        # Return updated character
        c.execute("""
            SELECT id, manga_id, name, description, role, avatar_url, created_at
            FROM manga_characters
            WHERE id = ?
        """, (character_id,))
        updated = c.fetchone()
        conn.close()
        
        return jsonify({
            'id': updated[0],
            'manga_id': updated[1],
            'name': updated[2],
            'description': updated[3],
            'role': updated[4],
            'avatar_url': updated[5],
            'created_at': updated[6]
        })
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 400


@app.route('/api/manga/character/<int:character_id>', methods=['DELETE'])
def delete_manga_character(character_id):
    """Delete a manga character."""
    if 'user_id' not in session:
        return jsonify({'error': 'login required'}), 401
    
    conn = get_conn()
    c = conn.cursor()
    
    # Get character and verify permissions
    c.execute("SELECT manga_id FROM manga_characters WHERE id = ?", (character_id,))
    char = c.fetchone()
    if not char:
        conn.close()
        return jsonify({'error': 'character not found'}), 404
    
    manga_id = char[0]
    c.execute("SELECT author FROM books WHERE id = ?", (manga_id,))
    manga = c.fetchone()
    
    user_id = session.get('user_id')
    c.execute("SELECT role FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    
    if user[0] not in ('admin', 'publisher') and manga[0] != user_id:
        conn.close()
        return jsonify({'error': 'permission denied'}), 403
    
    try:
        c.execute("DELETE FROM manga_characters WHERE id = ?", (character_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 400


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
    books_raw = c.fetchall()

    # Get user's favorite book IDs for showing heart icons
    user_favorites = set()
    if "user_id" in session:
        c.execute("SELECT book_id FROM favorites WHERE user_id = ?", (session["user_id"],))
        user_favorites = {row[0] for row in c.fetchall()}
    
    # Add favorite status to each book (as a boolean flag)
    books = []
    for book in books_raw:
        is_favorited = book[0] in user_favorites
        books.append(list(book) + [is_favorited])

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

@app.route("/admin/users", methods=["GET", "POST"], endpoint="user_management")
@admin_required
def admin_users():
    conn = get_conn()
    c = conn.cursor()

    c.execute("SELECT id, username, role, COALESCE(is_banned,0) as is_banned, COALESCE(status,'active') as status, COALESCE(avatar_url, NULL) as avatar_url, COALESCE(plan,'basic') as plan FROM users ORDER BY username")
    users = c.fetchall()

    c.execute("""
        SELECT rr.id, u.username, rr.requested_role, rr.created_at
        FROM role_requests rr
        JOIN users u ON rr.user_id = u.id
        WHERE rr.status = 'pending'
        ORDER BY rr.created_at ASC
    """)
    pending = c.fetchall()

    conn.close()
    return render_template("user_management.html", users=users, pending=pending)


@app.post("/admin/users/<int:user_id>/plan")
@admin_required
def admin_set_plan(user_id):
    plan = request.form.get("plan", "basic").strip().lower()
    if plan not in {"basic", "pro", "ultimate"}:
        flash("Invalid plan.", "danger")
        return redirect(url_for("user_management"))

    # Ultimate forever => plan_expires_at NULL
    expires_at = None
    if plan in {"basic", "pro"}:
        # you can set expiry later; keep NULL for now
        expires_at = None

    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE users SET plan=?, plan_expires_at=? WHERE id=?", (plan, expires_at, user_id))
    conn.commit()
    conn.close()

    flash(f"Plan updated to {plan}.", "success")
    return redirect(url_for("user_management"))


@app.route("/admin/team", methods=["GET", "POST"], endpoint="team_admin")
@admin_required
def team_admin():
    try:
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
        return render_template('team_admin.html', members=members)
    except Exception as e:
        # Log the traceback to server logs for debugging and show friendly message
        import traceback
        traceback.print_exc()
        try:
            conn.close()
        except Exception:
            pass
        flash(f"Error loading Team Admin: {str(e)}", "danger")
        return redirect(url_for('home'))
    return render_template("team_admin.html", members=members)

@app.post("/admin/team/<int:member_id>/delete", endpoint="team_delete")
@admin_required
def team_delete(member_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM team WHERE id=?", (member_id,))
    conn.commit()
    conn.close()
    flash("Team member deleted.", "success")
    return redirect(url_for("team_admin"))

@app.post("/admin/users/<int:user_id>/ban")
@admin_required
def user_ban(user_id):
    # prevent self-ban
    if user_id == session.get("user_id"):
        flash("You cannot ban yourself.", "danger")
        return redirect(url_for("user_management"))

    conn = get_conn()
    c = conn.cursor()

    # prevent banning admins
    c.execute("SELECT role FROM users WHERE id=?", (user_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        flash("User not found.", "danger")
        return redirect(url_for("user_management"))
    if row[0] == "admin":
        conn.close()
        flash("You cannot ban another admin.", "danger")
        return redirect(url_for("user_management"))

    c.execute("UPDATE users SET status='banned', is_banned=1 WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

    # Log admin action
    admin_id = session.get("user_id")
    log_system_event('WARNING', 'admin', f'Admin banned user ID {user_id}', admin_id, {'action': 'ban_user', 'target_user_id': user_id})

    flash("User banned.", "success")
    return redirect(url_for("user_management"))


@app.post("/admin/users/<int:user_id>/unban")
@admin_required
def user_unban(user_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE users SET status='active', is_banned=0 WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

    # Log admin action
    admin_id = session.get("user_id")
    log_system_event('INFO', 'admin', f'Admin unbanned user ID {user_id}', admin_id, {'action': 'unban_user', 'target_user_id': user_id})

    flash("User unbanned.", "success")
    return redirect(url_for("user_management"))


@app.post("/admin/users/<int:user_id>/delete")
@admin_required
def user_delete(user_id):
    if user_id == session.get("user_id"):
        flash("You cannot delete yourself.", "danger")
        return redirect(url_for("user_management"))

    conn = get_conn()
    c = conn.cursor()

    # prevent deleting admins
    c.execute("SELECT role FROM users WHERE id=?", (user_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        flash("User not found.", "danger")
        return redirect(url_for("user_management"))
    if row[0] == "admin":
        conn.close()
        flash("You cannot delete an admin.", "danger")
        return redirect(url_for("user_management"))

    c.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

    # Log admin action
    admin_id = session.get("user_id")
    log_system_event('CRITICAL', 'admin', f'Admin deleted user ID {user_id}', admin_id, {'action': 'delete_user', 'target_user_id': user_id})

    flash("User deleted.", "success")
    return redirect(url_for("user_management"))

# -------------------- FAQ ROUTE --------------------
@app.route("/faq")
def faq():
    """Display FAQ & Guidelines page"""
    return render_template("faq.html")


# -------------------- ERROR HANDLERS --------------------
@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file upload size limit exceeded"""
    flash("File upload failed: The uploaded file is too large. Please check file size limits.", "danger")
    return redirect(request.url)

# -------------------- MAIN --------------------
if __name__ == "__main__":
    init_db()
    # Bind to all interfaces and run without the reloader so external tests can connect reliably
    debug_env = os.environ.get('FLASK_DEBUG', os.environ.get('FLASK_ENV', '0'))
    debug_mode = str(debug_env).lower() in ('1', 'true', 'yes', 'debug')
    app.run(host='0.0.0.0', port=5000, debug=debug_mode, use_reloader=False)

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


# Development helper to run internal tests via HTTP (local use only)
@app.route('/_dev_run_manga_tests')
def _dev_run_manga_tests():
    if request.remote_addr not in ('127.0.0.1', '::1'):
        return jsonify({'error': 'forbidden'}), 403

    results = []
    try:
        from tests.test_manga_reader_features import (
            test_ai_summary_endpoint,
            test_manga_reader_template_contains_ui_elements,
        )
    except Exception as e:
        return jsonify({'error': 'import_failed', 'exc': str(e)}), 500

    for fn in (test_ai_summary_endpoint, test_manga_reader_template_contains_ui_elements):
        try:
            fn()
            results.append({'name': fn.__name__, 'ok': True})
        except AssertionError as ae:
            results.append({'name': fn.__name__, 'ok': False, 'err': str(ae)})
        except Exception as ex:
            results.append({'name': fn.__name__, 'ok': False, 'exc': str(ex)})

    return jsonify({'results': results})


# -------------------- IMAGE-TO-SUMMARY AI --------------------
try:
    from image_summary_ai import ImageSummaryAI
    IMAGE_AI_AVAILABLE = True
except ImportError:
    IMAGE_AI_AVAILABLE = False
    print('Warning: image_summary_ai module not found')


@app.route('/api/manga/page/<int:chapter_id>/<int:page_num>/summarize', methods=['POST'])
def summarize_manga_page(chapter_id, page_num):
    """Generate AI summary for a manga page image"""
    if 'user_id' not in session:
        return jsonify({'error': 'login required'}), 401
    
    if not IMAGE_AI_AVAILABLE:
        return jsonify({'error': 'AI summarization not available'}), 503
    
    try:
        conn = get_conn()
        c = conn.cursor()
        
        # Get chapter and verify access
        c.execute("""
            SELECT ch.id, ch.manga_id, b.id
            FROM chapters ch
            JOIN books b ON ch.manga_id = b.id
            WHERE ch.id = ?
        """, (chapter_id,))
        chapter_info = c.fetchone()
        
        if not chapter_info:
            conn.close()
            return jsonify({'error': 'chapter not found'}), 404
        
        # Construct image path
        manga_id = chapter_info[1]
        image_path = os.path.join(
            UPLOAD_FOLDER_MANGA,
            f"manga_{manga_id}",
            f"chapter_{chapter_id}",
            f"page_{page_num:03d}.jpg"
        )
        
        # Check if image exists
        if not os.path.exists(image_path):
            conn.close()
            return jsonify({'error': 'page image not found'}), 404
        
        # Generate summary
        ai = ImageSummaryAI()
        summary = ai.summarize_manga_page(image_path)
        
        # Store summary in database
        c.execute("""
            INSERT OR REPLACE INTO image_summaries 
            (chapter_id, page_num, image_path, summary)
            VALUES (?, ?, ?, ?)
        """, (chapter_id, page_num, image_path, summary))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'page_num': page_num,
            'summary': summary
        })
    
    except Exception as e:
        return jsonify({'error': f'Summarization failed: {str(e)}'}), 500
    
    
    @app.route('/api/manga/page/<int:chapter_id>/<int:page_num>/extract-text', methods=['POST'])
    def extract_manga_page_text(chapter_id, page_num):
        """Extract text from a manga page image"""
        if 'user_id' not in session:
            return jsonify({'error': 'login required'}), 401
        
        if not IMAGE_AI_AVAILABLE:
            return jsonify({'error': 'Text extraction not available'}), 503
        
        try:
            conn = get_conn()
            c = conn.cursor()
            
            # Get chapter info
            c.execute("""
                SELECT manga_id, chapter_num, pdf_filename
                FROM chapters
                WHERE id = ?
            """, (chapter_id,))
            chapter_info = c.fetchone()
            
            if not chapter_info:
                conn.close()
                return jsonify({'error': 'chapter not found'}), 404
            
            manga_id, chapter_num, pdf_filename = chapter_info
            
            # Get page files
            if pdf_filename and ',' in pdf_filename:
                page_files = pdf_filename.split(',')
            else:
                page_files = [pdf_filename] if pdf_filename else []
            
            if page_num < 1 or page_num > len(page_files):
                conn.close()
                return jsonify({'error': 'invalid page number'}), 400
            
            page_filename = page_files[page_num - 1]
            
            # Construct image path
            image_path = os.path.join(
                UPLOAD_FOLDER_MANGA,
                f"manga_{manga_id}_ch{chapter_num}",
                page_filename
            )
            
            # Check if image exists
            if not os.path.exists(image_path):
                conn.close()
                return jsonify({'error': 'page image not found'}), 404
            
            # Extract text
            ai = ImageSummaryAI()
            text = ai.extract_text_from_image(image_path)
            
            conn.close()
            
            return jsonify({
                'success': True,
                'page_num': page_num,
                'extracted_text': text
            })
        
        except Exception as e:
            return jsonify({'error': f'Text extraction failed: {str(e)}'}), 500
    
    
@app.route('/api/book/<int:book_id>/cover/analyze', methods=['POST'])
def analyze_book_cover(book_id):
    """Analyze book/manga cover image using AI"""
    if 'user_id' not in session:
        return jsonify({'error': 'login required'}), 401
    
    if not IMAGE_AI_AVAILABLE:
        return jsonify({'error': 'AI analysis not available'}), 503
    
    try:
        conn = get_conn()
        c = conn.cursor()
        
        # Get book and cover path
        c.execute("SELECT cover_path FROM books WHERE id = ?", (book_id,))
        book = c.fetchone()
        if not book or not book[0]:
            conn.close()
            return jsonify({'error': 'book or cover not found'}), 404
        
        cover_path = os.path.join(APP_ROOT, book[0].lstrip('/'))
        
        if not os.path.exists(cover_path):
            conn.close()
            return jsonify({'error': 'cover image not found'}), 404
        
        # Analyze cover
        ai = ImageSummaryAI()
        analysis = ai.summarize_book_cover(cover_path)
        
        conn.close()
        return jsonify({
            'success': True,
            'book_id': book_id,
            'analysis': analysis
        })
    
    except Exception as e:
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500


@app.route('/api/image/extract-text', methods=['POST'])
def extract_image_text():
    """Extract text from uploaded image"""
    if 'user_id' not in session:
        return jsonify({'error': 'login required'}), 401
    
    if not IMAGE_AI_AVAILABLE:
        return jsonify({'error': 'Text extraction not available'}), 503
    
    try:
        image_file = request.files.get('image')
        if not image_file:
            return jsonify({'error': 'no image provided'}), 400
        
        # Save temp image
        ext = image_file.filename.rsplit('.', 1)[-1].lower()
        if ext not in ALLOWED_IMG:
            return jsonify({'error': 'invalid image format'}), 400
        
        temp_filename = secure_filename(f"temp_{int(datetime.now().timestamp())}.{ext}")
        temp_path = os.path.join(APP_ROOT, 'static', 'temp', temp_filename)
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
        image_file.save(temp_path)
        
        # Extract text
        ai = ImageSummaryAI()
        text = ai.extract_text_from_image(temp_path)
        
        # Clean up temp file
        try:
            os.remove(temp_path)
        except:
            pass
        
        return jsonify({
            'success': True,
            'extracted_text': text
        })
    
    except Exception as e:
        return jsonify({'error': f'Text extraction failed: {str(e)}'}), 500
