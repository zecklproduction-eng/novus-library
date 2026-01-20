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
import traceback
import mimetypes
from logging.handlers import RotatingFileHandler
from werkzeug.utils import secure_filename
import re

# Add custom MIME types for code projects
mimetypes.add_type('application/javascript', '.js')
mimetypes.add_type('application/javascript', '.ts')
mimetypes.add_type('application/javascript', '.tsx')
mimetypes.add_type('application/javascript', '.jsx')

UPLOAD_FOLDER = os.path.join("static", "uploads", "avatars")
ALLOWED_EXTS = {"png", "jpg", "jpeg", "webp", "jfif"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Import AI error handling
import ai_error_fixes
from image_summary_ai import ImageSummaryAI

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
    # print('Warning: Python package "requests" not found. Optional features (OpenAI calls, external tests) will be disabled. Install with: pip install requests')
from werkzeug.utils import secure_filename
from functools import wraps
try:
    from pdf2image import convert_from_path
    PDF_EXTRACTION_AVAILABLE = True
except ImportError:
    PDF_EXTRACTION_AVAILABLE = False
    # print('Warning: pdf2image not available. PDF to image conversion will be disabled. Install with: pip install pdf2image')

try:
    from authlib.integrations.flask_client import OAuth
    AUTHLIB_AVAILABLE = True
except ImportError:
    OAuth = None
    AUTHLIB_AVAILABLE = False
    # print("Warning: Authlib not found. OAuth features disabled.")

# -------------------- PATHS / CONFIG --------------------
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_ROOT, "library.db")

UPLOAD_FOLDER_PDF    = os.path.join(APP_ROOT, "static", "books")
UPLOAD_FOLDER_AUDIO  = os.path.join(APP_ROOT, "static", "audio")
UPLOAD_FOLDER_COVERS = os.path.join(APP_ROOT, "static", "covers")
UPLOAD_FOLDER_MANGA  = os.path.join(APP_ROOT, "static", "manga")
UPLOAD_FOLDER_ANIMATIONS = os.path.join(APP_ROOT, "static", "animations")

os.makedirs(UPLOAD_FOLDER_PDF, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_AUDIO, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_COVERS, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_MANGA, exist_ok=True)


ALLOWED_PDF   = {"pdf"}
ALLOWED_AUDIO = {"mp3"}
ALLOWED_IMG   = {"jpg", "jpeg", "png", "webp", "jfif"}
ALLOWED_ANIMATION = {"mp4", "webm", "gif", "png", "jpg", "jpeg"}

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "novus_secret_key")
app.config['TEMPLATES_AUTO_RELOAD'] = True


# Custom Jinja filter for relative time display
@app.template_filter('time_ago')
def time_ago_filter(dt):
    """Convert datetime to relative time string like '2 hours ago'"""
    if not dt:
        return 'Just now'
    
    if isinstance(dt, str):
        try:
            dt = datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
        except:
            try:
                dt = datetime.strptime(dt, '%Y-%m-%d')
            except:
                return dt
    
    now = datetime.now()
    diff = now - dt
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return 'Just now'
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f'{minutes}m ago'
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f'{hours}h ago'
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f'{days}d ago'
    elif seconds < 2592000:
        weeks = int(seconds / 604800)
        return f'{weeks}w ago'
    else:
        return dt.strftime('%b %d, %Y')


@app.template_filter('format_count')
def format_count_filter(n):
    """Format large numbers as 1k, 1m, etc."""
    try:
        n = int(n or 0)
    except (ValueError, TypeError):
        return n
        
    if n < 1000:
        return str(n)
    if n < 1000000:
        val = n / 1000.0
        return f"{val:.1f}k".replace('.0k', 'k')
    if n < 1000000000:
        val = n / 1000000.0
        return f"{val:.1f}m".replace('.0m', 'm')
    val = n / 1000000000.0
    return f"{val:.1f}b".replace('.0b', 'b')


@app.template_filter('mentions')
def mentions_filter(text):
    """Highlight @usernames, #hashtags, etc. in text"""
    if not text:
        return text
    
    from markupsafe import escape
    text = str(escape(text))
    
    # Highlight @mentions
    mention_pattern = r'@([a-zA-Z0-9_-]+)'
    def replace_mention(match):
        username = match.group(1)
        if username in ['everyone', 'admin', 'publisher', 'mod']:
            return f'<span class="mention-tag role-mention">@{username}</span>'
        elif username.startswith('mod-'):
            actual_user = username[4:]
            return f'<span class="mention-tag mod-mention" title="Moderator: {actual_user}">@{username}</span>'
        else:
            return f'<span class="mention-tag user-mention">@{username}</span>'
            
    text = re.sub(mention_pattern, replace_mention, text)
    
    # Highlight #hashtags
    hashtag_pattern = r'#([a-zA-Z0-9_-]+)'
    def replace_hashtag(match):
        tag = match.group(1)
        return f'<a href="/community?q=%23{tag}" class="hashtag-link">#{tag}</a>'
        
    return re.sub(hashtag_pattern, replace_hashtag, text)



# Context Processor to make animations available globally (for banner in base/index)
@app.context_processor
def inject_animations():
    try:
        active_animations = {}
        animation_styles = {
            'login': 'standard',
            'manga': 'classic',
            'dashboard': 'none',
            'logout': 'fade'
        }
        
        # Avoid DB calls if not needed or if session missing
        if "user_id" in session:
            try:
                conn = get_conn()
                c = conn.cursor()
                # Get active custom animations
                c.execute("SELECT animation_type, file_path, name, COALESCE(has_animated, 0), category FROM custom_animations WHERE user_id = ? AND is_active = 1", (session["user_id"],))
                rows = c.fetchall()
                for row in rows:
                    active_animations[row[0]] = {
                        'path': row[1], 
                        'name': row[2],
                        'has_animated': row[3],
                        'category': row[4]
                    }
                
                # Get animation style settings
                c.execute("SELECT setting_key, setting_value FROM animation_settings WHERE user_id = ?", (session["user_id"],))
                settings_rows = c.fetchall()
                for row in settings_rows:
                    if row[0] in animation_styles:
                        animation_styles[row[0]] = row[1]
                conn.close()
            except Exception as db_err:
                logger.error(f"DB Error in inject_animations: {str(db_err)}")
            
        # We inject 'animations' as the active set and 'anim_styles' for style settings
        return dict(animations=active_animations, anim_styles=animation_styles)
    except Exception as e:
        logger.error(f"Error in inject_animations processor: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {'animations': {}, 'anim_styles': {}}

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
MAX_ANIMATION_SIZE = 100 * 1024 * 1024  # 100MB for animations

# Global Error Handlers for API JSON responses
@app.errorhandler(413)
def request_entity_too_large(error):
    if request.path.startswith('/api/') or request.is_json:
        return jsonify({"error": f"File too large. Max size is {app.config['MAX_CONTENT_LENGTH'] // (1024*1024)}MB"}), 413
    return "File too large", 413

@app.errorhandler(404)
def not_found_error(error):
    if request.path.startswith('/api/') or request.is_json:
        return jsonify({"error": "Resource not found"}), 404
    return "Not Found", 404

@app.errorhandler(500)
def internal_error(error):
    import traceback
    logger.error(f"500 Error: {error}\n{traceback.format_exc()}")
    if request.path.startswith('/api/') or request.is_json:
        return jsonify({"error": "Internal server error"}), 500
    return "Internal Server Error", 500




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

def apply_default_banner_if_needed(user_id):
    """
    Apply the Novus Blue preset banner as default if user has no active banner.
    This is called after successful login to ensure new users have a banner.
    """
    try:
        conn = get_conn()
        c = conn.cursor()
        
        # Check if user already has an active banner
        c.execute("SELECT id FROM custom_animations WHERE user_id = ? AND animation_type = 'banner' AND is_active = 1", (user_id,))
        existing_banner = c.fetchone()
        
        if not existing_banner:
            # User has no active banner, apply the Novus Blue banner as default (Animation #2)
            preset_path = 'img/banner_option_novus_blue.png'
            
            # Check if this preset already exists for the user (inactive)
            c.execute("SELECT id FROM custom_animations WHERE user_id = ? AND file_path = ?", (user_id, preset_path))
            existing_preset = c.fetchone()
            
            if existing_preset:
                # Activate existing preset
                c.execute("UPDATE custom_animations SET is_active = 1 WHERE id = ?", (existing_preset[0],))
            else:
                # Insert new preset banner
                c.execute("""
                    INSERT INTO custom_animations (user_id, animation_type, file_path, is_active, name, category)
                    VALUES (?, 'banner', ?, 1, 'Novus Blue', 'animation')
                """, (user_id, preset_path))
            
            conn.commit()
        
        conn.close()
    except Exception as e:
        logger.error(f"Error in apply_default_banner_if_needed for user {user_id}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

@app.before_request
def check_banned():
    try:
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
            try:
                if int(is_banned) == 1 or status == "banned":
                    session.clear()
                    flash("Your account has been banned.", "danger")
                    return redirect(url_for("login"))
            except (ValueError, TypeError) as e:
                 logger.error(f"Type conversion error for banned status for user {uid}: {e}")
    except Exception as e:
        logger.error(f"Error in check_banned: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())


# Context processor to make user avatar available globally
@app.context_processor
def inject_user_avatar():
    try:
        avatar_url = session.get('avatar_url')
        # Add /static/ prefix if needed
        if avatar_url and not avatar_url.startswith('http') and not avatar_url.startswith('/'):
            avatar_url = '/static/' + avatar_url
        return {
            'user_avatar': avatar_url,
            'user_id': session.get('user_id')
        }
    except Exception as e:
        logger.error(f"Error in inject_user_avatar context processor: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {'user_avatar': None, 'user_id': None}


def allowed(filename, allowed_set):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_set


def admin_required(f):
    """Allow only admin to access the route."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            if session.get("role") != "admin":
                flash("Admin access required.", "danger")
                return redirect(url_for("logout"))
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in admin_required decorator: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            flash("An unexpected error occurred.", "danger")
            return redirect(url_for("home"))
    return wrapper


def login_required(f):
    """Allow any logged in user to access the route."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            if "user_id" not in session:
                flash("Please log in to access this page.", "info")
                return redirect(url_for("login"))
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in login_required decorator: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            flash("An unexpected error occurred.", "danger")
            return redirect(url_for("home"))
    return wrapper


def role_required(*roles):
    """Allow only the given roles to access the route."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                if session.get("role") not in roles:
                    flash("You do not have permission to access this page.", "danger")
                    return redirect(url_for("home"))
                return f(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in role_required decorator: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                flash("An unexpected error occurred.", "danger")
                return redirect(url_for("home"))
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

    # Add custom_summary column if it doesn't exist (migration)
    try:
        c.execute("ALTER TABLE books ADD COLUMN custom_summary TEXT")
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

    # reading_history
    c.execute("""
        CREATE TABLE IF NOT EXISTS reading_history (
            user_id INTEGER,
            manga_id INTEGER,
            chapter_id INTEGER,
            page_index INTEGER,
            updated_at TIMESTAMP,
            PRIMARY KEY (user_id, manga_id),
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(manga_id) REFERENCES books(id)
        )
    """)

    # Ensure reading_history has updated_at and page_index (migration)
    try:
        c.execute("ALTER TABLE reading_history ADD COLUMN updated_at TIMESTAMP")
        conn.commit()
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE reading_history ADD COLUMN page_index INTEGER DEFAULT 0")
        conn.commit()
    except sqlite3.OperationalError:
        pass
    
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

    # Review migrations
    try:
        c.execute("ALTER TABLE reviews ADD COLUMN has_spoilers BOOLEAN DEFAULT 0")
        conn.commit()
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE reviews ADD COLUMN status TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    # review likes (helpful votes)
    c.execute("""
        CREATE TABLE IF NOT EXISTS review_likes (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            review_id INTEGER NOT NULL,
            created_at TEXT DEFAULT (DATETIME('now')),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (review_id) REFERENCES reviews(id),
            UNIQUE(user_id, review_id)
        )
    """)

    # review comments
    c.execute("""
        CREATE TABLE IF NOT EXISTS review_comments (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            review_id INTEGER NOT NULL,
            parent_id INTEGER, -- For nested replies
            content TEXT,
            created_at TEXT DEFAULT (DATETIME('now')),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (review_id) REFERENCES reviews(id),
            FOREIGN KEY (parent_id) REFERENCES review_comments(id)
        )
    """)

    # Review comment likes
    c.execute("""
        CREATE TABLE IF NOT EXISTS comment_likes (
            user_id INTEGER NOT NULL,
            comment_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, comment_id),
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(comment_id) REFERENCES review_comments(id)
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

    # manga reading progress
    c.execute("""
        CREATE TABLE IF NOT EXISTS manga_progress (
            id         INTEGER PRIMARY KEY,
            user_id    INTEGER NOT NULL,
            manga_id   INTEGER NOT NULL,
            chapter_id INTEGER NOT NULL,
            page_index INTEGER DEFAULT 0,
            updated_at TEXT DEFAULT (DATETIME('now')),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (manga_id) REFERENCES books(id),
            FOREIGN KEY (chapter_id) REFERENCES chapters(id),
            UNIQUE(user_id, manga_id)
        )
    """)

    # custom animations table
    c.execute("""
        CREATE TABLE IF NOT EXISTS custom_animations (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            animation_type TEXT NOT NULL,
            file_path TEXT NOT NULL,
            is_active INTEGER DEFAULT 0,
            has_animated INTEGER DEFAULT 0,
            name TEXT,
            category TEXT DEFAULT 'animation',
            min_plan TEXT DEFAULT 'basic',
            accent_color TEXT,
            created_at TEXT DEFAULT (DATETIME('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Add category column to custom_animations if it doesn't exist
    try:
        c.execute("ALTER TABLE custom_animations ADD COLUMN category TEXT DEFAULT 'animation'")
        conn.commit()
    except sqlite3.OperationalError:
        pass
        
    # Add name and access_tag columns
    try:
        c.execute("ALTER TABLE custom_animations ADD COLUMN name TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE custom_animations ADD COLUMN access_tag TEXT DEFAULT 'basic'")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    try:
        c.execute("ALTER TABLE custom_animations ADD COLUMN has_animated INTEGER DEFAULT 0")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    try:
        c.execute("ALTER TABLE custom_animations ADD COLUMN min_plan TEXT DEFAULT 'basic'")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    try:
        c.execute("ALTER TABLE custom_animations ADD COLUMN accent_color TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass
        
    conn.commit()

    # animation settings table (for style preferences like 'glitch', 'warp', 'shutter')
    c.execute("""
        CREATE TABLE IF NOT EXISTS animation_settings (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            setting_key TEXT NOT NULL,
            setting_value TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, setting_key)
        )
    """)

    # support/requests table
    c.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            item_type TEXT NOT NULL,
            manga_id INTEGER, -- For chapter requests
            author TEXT,
            notes TEXT,

            status TEXT DEFAULT 'Requested',
            vote_count INTEGER DEFAULT 0,
            fulfilled_by INTEGER,
            created_at TEXT DEFAULT (DATETIME('now')),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (manga_id) REFERENCES books(id),
            FOREIGN KEY (fulfilled_by) REFERENCES users(id)
        )
    """)

    # Migration for requests table
    try:
        c.execute("ALTER TABLE requests ADD COLUMN manga_id INTEGER")
        conn.commit()
    except sqlite3.OperationalError:
        pass
    
    try:
        c.execute("ALTER TABLE requests ADD COLUMN fulfilled_by INTEGER")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    # request votes tracking (to prevent double voting)
    c.execute("""
        CREATE TABLE IF NOT EXISTS request_votes (
            id INTEGER PRIMARY KEY,
            request_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            vote_value INTEGER DEFAULT 1,
            FOREIGN KEY (request_id) REFERENCES requests(id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(request_id, user_id)
        )
    """)

    # publisher earnings from requests
    c.execute("""
        CREATE TABLE IF NOT EXISTS publisher_earnings (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            request_id INTEGER, -- Optional, if for a request
            amount REAL NOT NULL,
            reason TEXT,
            created_at TEXT DEFAULT (DATETIME('now')),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (request_id) REFERENCES requests(id)
        )
    """)

    # bundles table (preset configurations)
    c.execute("""
        CREATE TABLE IF NOT EXISTS bundles (
            id INTEGER PRIMARY KEY,
            slug TEXT UNIQUE,
            name TEXT NOT NULL,
            description TEXT,
            min_plan TEXT DEFAULT 'basic',
            includes_json TEXT,
            theme_json TEXT,
            banner_preset TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (DATETIME('now'))
        )
    """)

    # Migration for bundles table
    try:
        c.execute("ALTER TABLE bundles ADD COLUMN min_plan TEXT DEFAULT 'basic'")
        conn.commit()
    except sqlite3.OperationalError:
        pass
    
    # Add icon_path column for bundle icons
    try:
        c.execute("ALTER TABLE bundles ADD COLUMN icon_path TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    # Seed default bundles if table is empty
    c.execute("SELECT COUNT(*) FROM bundles")
    if c.fetchone()[0] == 0:
        import json
        default_bundles = [
            {
                "slug": "manga-starter",
                "name": "Manga Starter",
                "description": "Warp + neon vibes. Great default preset with animated transitions.",
                "includes": [
                    "Banner preset: Glow strip",
                    "Theme preset: Dark + cyan accent",
                    "Animations: ON • Transitions: ON",
                    "Login/Logout: Styled buttons + overlay"
                ],
                "theme": {
                    "theme": "dark",
                    "accentColor": "cyan",
                    "fontSize": "medium",
                    "density": "comfortable",
                    "smoothScroll": True,
                    "pageTransitions": True,
                    "animations": True,
                    "uiEffects": True,
                    "specialEffects": True
                },
                "banner_preset": "glow-strip",
                "colors": ["#0d1117", "#161b22", "#21262d", "#00d4ff", "#58a6ff", "#c9a0dc"]
            },
            {
                "slug": "minimal-reader",
                "name": "Minimal Reader",
                "description": "No animations, clean interface. Perfect for distraction-free reading.",
                "includes": [
                    "Banner preset: None (clean)",
                    "Theme preset: Dark minimal",
                    "Animations: OFF • Transitions: OFF",
                    "Login/Logout: Standard buttons"
                ],
                "theme": {
                    "theme": "dark",
                    "accentColor": "cyan",
                    "fontSize": "medium",
                    "density": "comfortable",
                    "smoothScroll": False,
                    "pageTransitions": False,
                    "animations": False,
                    "uiEffects": False,
                    "specialEffects": False
                },
                "banner_preset": "none",
                "colors": ["#0d1117", "#161b22", "#21262d", "#6e7681", "#8b949e", "#c9d1d9"]
            },
            {
                "slug": "neon-night",
                "name": "Neon Night",
                "description": "Animated with high contrast and purple neon accents. Bold and vibrant.",
                "includes": [
                    "Banner preset: Neon pulse",
                    "Theme preset: Dark + purple accent",
                    "Animations: ON • Transitions: ON",
                    "Login/Logout: Glow buttons + overlay"
                ],
                "theme": {
                    "theme": "purple",
                    "accentColor": "purple",
                    "fontSize": "medium",
                    "density": "comfortable",
                    "smoothScroll": True,
                    "pageTransitions": True,
                    "animations": True,
                    "uiEffects": True,
                    "specialEffects": True
                },
                "banner_preset": "neon-pulse",
                "colors": ["#0d0d1a", "#1a1a2e", "#16213e", "#667eea", "#764ba2", "#c9a0dc"]
            },
            {
                "slug": "cozy-sepia",
                "name": "Cozy Sepia",
                "description": "Warm paper tones for long reading sessions. Soft and easy on the eyes.",
                "includes": [
                    "Banner preset: Warm gradient",
                    "Theme preset: Warm sepia tones",
                    "Animations: Soft • Transitions: ON",
                    "Login/Logout: Warm styled buttons"
                ],
                "theme": {
                    "theme": "sunset",
                    "accentColor": "orange",
                    "fontSize": "medium",
                    "density": "comfortable",
                    "smoothScroll": True,
                    "pageTransitions": True,
                    "animations": True,
                    "uiEffects": True,
                    "specialEffects": False
                },
                "banner_preset": "warm-gradient",
                "colors": ["#1a0a0a", "#2d1810", "#3d2817", "#d4a373", "#e9c46a", "#f4d58d"]
            },
            {
                "slug": "classic-dark",
                "name": "Classic Dark",
                "description": "Standard dark theme with subtle accents. Transitions enabled, solid design.",
                "includes": [
                    "Banner preset: Subtle shadow",
                    "Theme preset: Classic dark",
                    "Animations: OFF • Transitions: ON",
                    "Login/Logout: Standard styling"
                ],
                "theme": {
                    "theme": "dark",
                    "accentColor": "indigo",
                    "fontSize": "medium",
                    "density": "comfortable",
                    "smoothScroll": True,
                    "pageTransitions": True,
                    "animations": False,
                    "uiEffects": True,
                    "specialEffects": False
                },
                "banner_preset": "subtle-shadow",
                "colors": ["#0d1117", "#161b22", "#21262d", "#6366f1", "#4338ca", "#818cf8"]
            }
        ]
        
        for bundle in default_bundles:
            c.execute("""
                INSERT INTO bundles (slug, name, description, includes_json, theme_json, banner_preset)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                bundle["slug"],
                bundle["name"],
                bundle["description"],
                json.dumps(bundle["includes"]),
                json.dumps({**bundle["theme"], "colors": bundle["colors"]}),
                bundle["banner_preset"]
            ))
        conn.commit()

    # manga_reviews table
    c.execute("""
        CREATE TABLE IF NOT EXISTS manga_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            manga_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            chapter_id INTEGER,
            content TEXT NOT NULL,
            rating INTEGER DEFAULT 5,
            has_spoilers BOOLEAN DEFAULT 0,
            status TEXT DEFAULT 'Reading',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (manga_id) REFERENCES books(id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (chapter_id) REFERENCES chapters(id),
            UNIQUE(manga_id, user_id)
        )
    """)
    # Migration for existing manga_reviews table
    for col, col_type in [("chapter_id", "INTEGER"), ("has_spoilers", "BOOLEAN DEFAULT 0"), ("status", "TEXT DEFAULT 'Reading'")]:
        try:
            c.execute(f"ALTER TABLE manga_reviews ADD COLUMN {col} {col_type}")
        except sqlite3.OperationalError:
            pass
    conn.commit()

    # tool_links table
    c.execute("""
        CREATE TABLE IF NOT EXISTS tool_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            description TEXT,
            category TEXT,
            plan_required TEXT DEFAULT 'basic',
            icon_type TEXT,
            icon_value TEXT,
            is_project INTEGER DEFAULT 0,
            project_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Migration for existing tool_links table
    c.execute("PRAGMA table_info(tool_links)")
    columns = [col[1] for col in c.fetchall()]
    if 'is_project' not in columns:
        c.execute("ALTER TABLE tool_links ADD COLUMN is_project INTEGER DEFAULT 0")
        logger.info("Added 'is_project' column to tool_links table")
    if 'project_name' not in columns:
        c.execute("ALTER TABLE tool_links ADD COLUMN project_name TEXT")
        logger.info("Added 'project_name' column to tool_links table")

    # Seed default tool links if table is empty
    c.execute("SELECT COUNT(*) FROM tool_links")
    if c.fetchone()[0] == 0:
        default_links = [
            ('Google Workspace', 'https://workspace.google.com', 'Create workspace for your organization', 'work', 'basic', 'img', 'https://upload.wikimedia.org/wikipedia/commons/2/2f/Google_2015_logo.svg'),
            ('Figma - Design Tool', 'https://figma.com', 'Design innovation website', 'tools', 'basic', 'img', 'https://upload.wikimedia.org/wikipedia/commons/3/33/Figma-logo.svg'),
            ('GitHub - Repositories', 'https://github.com', 'GitHub website - repositories', 'work', 'basic', 'fa', 'fab fa-github'),
            ('YouTube', 'https://youtube.com', 'Watch videos and stream content', 'social', 'basic', 'fa', 'fab fa-youtube'),
            ('Twitter / X', 'https://x.com', 'Social networking platform', 'social', 'basic', 'fa', 'fab fa-twitter'),
            ('Notion', 'https://notion.so', 'All-in-one workspace for notes', 'work', 'basic', 'img', 'https://upload.wikimedia.org/wikipedia/commons/4/45/Notion_app_logo.png'),
            ('Discord', 'https://discord.com', 'Chat and communicate with friends', 'social', 'basic', 'fa', 'fab fa-discord'),
            ('VS Code Web', 'https://vscode.dev', 'Code editor in your browser', 'tools', 'basic', 'fa', 'fas fa-code'),
            ('ChatGPT', 'https://chat.openai.com', 'AI assistant for conversations', 'tools', 'basic', 'fa', 'fas fa-robot'),
            ('Canva', 'https://canva.com', 'Create stunning designs easily', 'tools', 'basic', 'fa', 'fas fa-palette'),
            ('Slack', 'https://slack.com', 'Team communication platform', 'work', 'basic', 'fa', 'fab fa-slack')
        ]
        c.executemany("""
            INSERT INTO tool_links (name, url, description, category, plan_required, icon_type, icon_value)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, default_links)
        conn.commit()

    # -------------------- COMMUNITY GROUPS TABLES --------------------
    # community_groups table - stores all community groups (genre, manga, book)
    c.execute("""
        CREATE TABLE IF NOT EXISTS community_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            group_type TEXT NOT NULL DEFAULT 'general',
            reference_id INTEGER,
            category TEXT,
            icon_url TEXT,
            banner_url TEXT,
            owner_id INTEGER,
            member_count INTEGER DEFAULT 0,
            post_count INTEGER DEFAULT 0,
            is_auto_created BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (owner_id) REFERENCES users(id)
        )
    """)

    # group_members table - stores group memberships
    c.execute("""
        CREATE TABLE IF NOT EXISTS group_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            role TEXT DEFAULT 'member',
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(group_id, user_id),
            FOREIGN KEY (group_id) REFERENCES community_groups(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

     # group_posts table - stores posts in groups
    c.execute("""
        CREATE TABLE IF NOT EXISTS group_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            title TEXT,
            content TEXT,
            post_type TEXT DEFAULT 'discussion',
            upvotes INTEGER DEFAULT 0,
            downvotes INTEGER DEFAULT 0,
            comment_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (group_id) REFERENCES community_groups(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # group_posts migration: add missing columns
    columns_to_add = [
        ("channel_id", "INTEGER"),
        ("manga_id", "INTEGER"),
        ("gif_url", "TEXT"),
        ("poll_question", "TEXT")
    ]
    for col_name, col_type in columns_to_add:
        try:
            c.execute(f"ALTER TABLE group_posts ADD COLUMN {col_name} {col_type}")
            conn.commit()
        except sqlite3.OperationalError:
            pass

    # poll_options table
    c.execute("""
        CREATE TABLE IF NOT EXISTS poll_options (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            option_text TEXT NOT NULL,
            vote_count INTEGER DEFAULT 0,
            FOREIGN KEY (post_id) REFERENCES group_posts(id) ON DELETE CASCADE
        )
    """)


    # group_post_attachments
    c.execute("""
        CREATE TABLE IF NOT EXISTS group_post_attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            file_url TEXT NOT NULL,
            file_type TEXT NOT NULL,
            file_name TEXT,
            FOREIGN KEY (post_id) REFERENCES group_posts(id) ON DELETE CASCADE
        )
    """)

    # group_post_votes
    c.execute("""
        CREATE TABLE IF NOT EXISTS group_post_votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            vote INTEGER NOT NULL, -- 1 for upvote, -1 for downvote
            UNIQUE(post_id, user_id),
            FOREIGN KEY (post_id) REFERENCES group_posts(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # group_comments
    c.execute("""
        CREATE TABLE IF NOT EXISTS group_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES group_posts(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # group_comment_attachments
    c.execute("""
        CREATE TABLE IF NOT EXISTS group_comment_attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            comment_id INTEGER NOT NULL,
            file_url TEXT NOT NULL,
            file_type TEXT NOT NULL,
            file_name TEXT,
            manga_id INTEGER,
            manga_title TEXT,
            manga_cover TEXT,
            FOREIGN KEY (comment_id) REFERENCES group_comments(id) ON DELETE CASCADE
        )
    """)

    # Migration: Add manga columns to group_comment_attachments if they don't exist
    try:
        c.execute("ALTER TABLE group_comment_attachments ADD COLUMN manga_id INTEGER")
        conn.commit()
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE group_comment_attachments ADD COLUMN manga_title TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE group_comment_attachments ADD COLUMN manga_cover TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    # group_comment_likes
    c.execute("""
        CREATE TABLE IF NOT EXISTS group_comment_likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            comment_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            reaction_type TEXT DEFAULT 'like',
            UNIQUE(comment_id, user_id),
            FOREIGN KEY (comment_id) REFERENCES group_comments(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    # Migration: Add reaction_type to group_comment_likes
    try:
        c.execute("ALTER TABLE group_comment_likes ADD COLUMN reaction_type TEXT DEFAULT 'like'")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    # group_channels
    c.execute("""
        CREATE TABLE IF NOT EXISTS group_channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            channel_type TEXT DEFAULT 'text',
            icon TEXT DEFAULT 'hash',
            position INTEGER DEFAULT 0,
            FOREIGN KEY (group_id) REFERENCES community_groups(id) ON DELETE CASCADE
        )
    """)

    # group_polls table
    c.execute("""
        CREATE TABLE IF NOT EXISTS group_polls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            question TEXT NOT NULL,
            allow_multiple BOOLEAN DEFAULT 0,
            expires_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES group_posts(id) ON DELETE CASCADE
        )
    """)

    # group_poll_options table
    c.execute("""
        CREATE TABLE IF NOT EXISTS group_poll_options (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            poll_id INTEGER NOT NULL,
            option_text TEXT NOT NULL,
            vote_count INTEGER DEFAULT 0,
            FOREIGN KEY (poll_id) REFERENCES group_polls(id) ON DELETE CASCADE
        )
    """)

    # group_poll_votes table
    c.execute("""
        CREATE TABLE IF NOT EXISTS group_poll_votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            poll_id INTEGER NOT NULL,
            option_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(poll_id, user_id, option_id),
            FOREIGN KEY (poll_id) REFERENCES group_polls(id) ON DELETE CASCADE,
            FOREIGN KEY (option_id) REFERENCES group_poll_options(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    conn.commit()

    # Seed default genre groups if none exist
    c.execute("SELECT COUNT(*) FROM community_groups WHERE group_type = 'genre'")
    if c.fetchone()[0] == 0:
        default_genre_groups = [
            ('Action', 'Discuss your favorite action manga and anime!', 'genre', 'Action', None),
            ('Romance', 'For fans of love stories and romantic manga!', 'genre', 'Romance', None),
            ('Fantasy', 'Explore magical worlds and fantastical adventures!', 'genre', 'Fantasy', None),
            ('Sci-Fi', 'Science fiction, mecha, and futuristic stories!', 'genre', 'Sci-Fi', None),
            ('Comedy', 'Laugh together with comedy manga fans!', 'genre', 'Comedy', None),
            ('Horror', 'For those who love a good scare!', 'genre', 'Horror', None),
            ('Slice of Life', 'Everyday life stories and chill reads!', 'genre', 'Slice of Life', None),
            ('Sports', 'Sports manga and anime discussions!', 'genre', 'Sports', None),
            ('Mystery', 'Detective stories and thrilling mysteries!', 'genre', 'Mystery', None),
            ('Adventure', 'Epic journeys and adventures await!', 'genre', 'Adventure', None),
        ]
        c.executemany("""
            INSERT INTO community_groups (name, description, group_type, category, owner_id, is_auto_created)
            VALUES (?, ?, ?, ?, ?, 1)
        """, default_genre_groups)
        conn.commit()
        logger.info("Created default genre groups for community")

    # Check/Create World Group
    c.execute("SELECT id FROM community_groups WHERE name = 'World' AND group_type = 'system'")
    if not c.fetchone():
        c.execute("""
            INSERT INTO community_groups (name, description, group_type, category, owner_id, is_auto_created)
            VALUES (?, ?, ?, ?, ?, 1)
        """, ('World', 'Global posts visible to everyone', 'system', 'General', None))
        conn.commit()
        logger.info("Created World system group")

    # Sync all users to World Group
    c.execute("SELECT id FROM community_groups WHERE name = 'World' AND group_type = 'system' LIMIT 1")
    world_row = c.fetchone()
    if world_row:
        world_group_id = world_row[0]
        # Insert users who are not yet members of the World group
        c.execute("""
            INSERT INTO group_members (group_id, user_id, role)
            SELECT ?, id, 'member'
            FROM users
            WHERE id NOT IN (SELECT user_id FROM group_members WHERE group_id = ?)
        """, (world_group_id, world_group_id))
        
        # Update World group member count
        c.execute("SELECT COUNT(*) FROM group_members WHERE group_id = ?", (world_group_id,))
        count = c.fetchone()[0]
        c.execute("UPDATE community_groups SET member_count = ? WHERE id = ?", (count, world_group_id))
        conn.commit()
        logger.info(f"Synced {count} users to World system group")

    conn.close()
    
    # Sync groups with existing content
    sync_community_groups()



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
    c.execute("SELECT DISTINCT COALESCE(category,'General') FROM books")
    db_raw_categories = [row[0] for row in c.fetchall()]
    
    db_categories = set()
    for cat_str in db_raw_categories:
        for cat in cat_str.split(','):
            cleaned = cat.strip()
            if cleaned:
                db_categories.add(cleaned)

    extra_categories = [
        "Action", "Adventure", "Biography", "Business", "Children", "Comedy", 
        "Cooking", "Crime", "Cyberpunk", "Documentary", "Drama", "Dystopian", 
        "Fantasy", "General", "Graphic Novel", "Health", "Historical", "Horror", 
        "Isekai", "Josei", "Lifestyle", "Magic", "Martial Arts", "Mecha", 
        "Memoir", "Mystery", "Philosophy", "Poetry", "Politics", "Psychological", 
        "Religion", "Romance", "School Life", "Science", "Science Fiction", 
        "Seinen", "Shoujo", "Shounen", "Slice of Life", "Sports", "Supernatural", 
        "Suspense", "Technology", "Thriller", "Travel", "Vampire", "Western", 
        "Young Adult"
    ]
    categories = sorted(set(list(db_categories) + extra_categories + ["General"]))

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
        # Improved search for multi-category support
        # We wrap both the column and the search term in commas to ensure exact word matching
        # e.g. "Action, Adventure" -> ",Action,Adventure," LIKE "%,Adventure,%"
        # We perform replace to handle any potential spaces in legacy data
        base_sql += " AND ',' || REPLACE(COALESCE(category,'General'), ' ', '') || ',' LIKE ?"
        params.append(f"%,{selected.replace(' ', '')},%")

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
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({"status": "error", "message": "Invalid username or password."}), 401
            return render_template("login.html", error="Invalid username or password.")

        # user[4] = is_banned (0/1), user[5] = status ('active'/'banned')
        if int(user[4]) == 1 or user[5] == "banned":
            # Log banned user login attempt
            log_system_event('WARNING', 'auth', f'Banned user {user[1]} attempted to login', user[0])
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({"status": "error", "message": "Your account has been banned."}), 403
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
        
        # Apply default banner if user doesn't have one
        apply_default_banner_if_needed(user[0])

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Fetch login animation settings
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("SELECT setting_value FROM animation_settings WHERE user_id = ? AND setting_key = 'login'", (user[0],))
            style_row = cur.fetchone()
            login_style = style_row[0] if style_row else 'standard'
            
            cur.execute("SELECT file_path FROM custom_animations WHERE user_id = ? AND animation_type = 'login' AND is_active = 1", (user[0],))
            custom_row = cur.fetchone()
            custom_anim = custom_row[0] if custom_row else None
            conn.close()

            return jsonify({
                "status": "success", 
                "redirect": url_for("home"),
                "login_style": login_style,
                "custom_anim": custom_anim
            })

        return redirect(url_for("home"))

    response = make_response(render_template("login.html"))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# ---------- Forgot Password ----------
@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip()
        
        if not email or "@" not in email:
            return render_template("forgot_password.html", error="Please enter a valid email address.")
        
        # Check if email exists in database
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT id, username FROM users WHERE email=?", (email,))
        user = c.fetchone()
        conn.close()
        
        if user:
            # Log the password reset request
            log_system_event('INFO', 'auth', f'Password reset requested for email: {email}', user[0])
            # In production, you would send an email with a reset link here
            return render_template("forgot_password.html", 
                success="If an account exists with this email, you will receive a password reset link shortly.")
        else:
            # Don't reveal if email exists or not for security
            return render_template("forgot_password.html", 
                success="If an account exists with this email, you will receive a password reset link shortly.")
    
    return render_template("forgot_password.html")

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
    
    # Apply default banner if user doesn't have one
    apply_default_banner_if_needed(user_id)
    
    return redirect(url_for("home"))

@app.before_request
def refresh_plan():
    try:
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
                    exp_str = session.get("plan_expires_at")
                    if exp_str:
                        # Try parsing as ISO format first, then fallback to date only
                        try:
                            exp_dt = datetime.fromisoformat(exp_str)
                        except ValueError:
                            exp_dt = datetime.strptime(exp_str, "%Y-%m-%d")
                        now = datetime.utcnow()
                        delta = exp_dt - now
                        session["plan_days_left"] = max(0, delta.days)
            except Exception as e:
                logger.error(f"Error computing plan days left for user {uid}: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
    except Exception as e:
        logger.error(f"Error in refresh_plan: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

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
        # Default all new users to 'reader'. If 'publisher' is requested, we create a role_request.
        role = "reader"
        requested_publisher = (account_type == "publisher")

        # Insert into DB
        conn = get_conn()
        c = conn.cursor()
        try:
            c.execute(
                "INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)",
                (username, email, password, role)
            )
            new_user_id = c.lastrowid
            
            # Create role request if publisher was selected
            if requested_publisher:
                c.execute(
                    "INSERT INTO role_requests (user_id, requested_role, status) VALUES (?, 'publisher', 'pending')",
                    (new_user_id,)
                )
            
            conn.commit()
        except sqlite3.IntegrityError as e:
            # Check which field caused the duplicate
            conn.close()
            if "username" in str(e):
                flash("That username is already taken.", "danger")
            elif "email" in str(e):
                flash("That email is already registered.", "danger")
            else:
                flash(f"Error registering user: {e}", "danger")
            return redirect(url_for("register"))
        finally:
            if conn:
                conn.close()

        # Flash appropriate message
        if requested_publisher:
             flash("Account created! Your publisher access request has been sent to admins for approval. You can login as a reader in the meantime.", "info")
        else:
             flash("Account created successfully! Please login.", "success")
        
        return redirect(url_for("login"))


        # Get the user id we just created
        c.execute("SELECT id, role FROM users WHERE username=?", (username,))
        row = c.fetchone()
        conn.close()

        # Log the user in
        session["user_id"] = row[0]
        session["username"] = username
        session["role"] = row[1]

        # Ensure user is in World group
        try:
            conn_g = get_conn()
            c_g = conn_g.cursor()
            c_g.execute("SELECT id FROM community_groups WHERE name = 'World' AND group_type = 'system' LIMIT 1")
            w_row = c_g.fetchone()
            if w_row:
                w_id = w_row[0]
                c_g.execute("INSERT OR IGNORE INTO group_members (group_id, user_id, role) VALUES (?, ?, 'member')", (w_id, session["user_id"]))
                c_g.execute("UPDATE community_groups SET member_count = member_count + 1 WHERE id = ?", (w_id,))
                conn_g.commit()
            conn_g.close()
        except Exception as e:
            logger.error(f"Error adding new user to World group: {e}")

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
@login_required
def view_book(id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_conn()
    c = conn.cursor()

    # fetch book
    c.execute(
        "SELECT id, title, author, category, pdf_filename, audio_filename, cover_path, description, transcript, toc, custom_summary FROM books WHERE id=?",
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
    
    # fetch rating stats
    c.execute("SELECT COUNT(*), AVG(rating) FROM reviews WHERE book_id=?", (id,))
    stats = c.fetchone()
    review_count = stats[0] if stats else 0
    avg_rating = stats[1] if stats else 0

    conn.close()

    # map DB status -> pretty label
    status_labels = {
        "watching": "Watching",
        "on_hold": "On-Hold",
        "planned": "Plan to Watch",
        "dropped": "Dropped",
        "completed": "Completed",
    }

    # Prepare cover URL for main book
    main_cover_path = book[6]
    if main_cover_path:
        main_cover_url = main_cover_path if main_cover_path.startswith(('http://', 'https://')) else f"/static/{main_cover_path}"
    else:
        main_cover_url = None

    # Prepare cover URLs for recommendations
    formatted_recs = []
    for r in recommendations:
        r_id, r_title, r_author, r_cat, r_cover = r
        if r_cover:
            r_img = r_cover if r_cover.startswith(('http://', 'https://')) else f"/static/{r_cover}"
        else:
            r_img = None
        formatted_recs.append((r_id, r_title, r_author, r_cat, r_img))

    # Prepare cover URLs for top wishlisted
    formatted_wishlisted = []
    for r in top_wishlisted:
        # Check if cover_path exists in the tuple (it depends on the query)
        # c.execute("SELECT b.id, b.title, b.category, b.cover_path, COUNT(*) as cnt ...")
        w_id, w_title, w_cat, w_cover, w_cnt = r
        if w_cover:
            w_img = w_cover if w_cover.startswith(('http://', 'https://')) else f"/static/{w_cover}"
        else:
            w_img = None
        formatted_wishlisted.append((w_id, w_title, w_cat, w_img, w_cnt))

    return render_template(
        "book_detail.html",
        book=book,
        cover_url=main_cover_url,
        reviews=reviews,
        recommendations=formatted_recs,
        top_wishlisted=formatted_wishlisted,
        is_favorited=is_favorited,
        status_labels=status_labels,
        current_status=current_status,
        review_count=review_count,
        avg_rating=avg_rating
    )


# ---------- Read Book (React PDF Reader) ----------
@app.route("/read/<int:id>")
@login_required
def read_book(id):
    """Serve the React PDF reader for a specific book."""
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    book = conn.execute('SELECT id, title, author, cover_path, audio_filename, transcript, custom_summary, pdf_filename, toc, uploader_id FROM books WHERE id = ?', (id,)).fetchone()
    conn.close()

    if book is None:
        flash("Book not found.", "danger")
        return redirect(url_for("home"))

    # Check if the current user is the publisher or an admin
    user_id = session.get('user_id')
    user_role = session.get('role')
    is_editor = (user_id == book['uploader_id']) or (user_role == 'admin')

    # Prepare URLs - PDFs are in /static/books/, audio in /static/audio/
    pdf_url = f"/static/books/{book['pdf_filename']}" if book['pdf_filename'] else ""
    
    # Fix cover path
    cover_path = book['cover_path']
    if cover_path and cover_path.startswith('http'):
         cover_url = cover_path
    elif cover_path:
         cover_url = url_for('static', filename=cover_path)
    else:
         cover_url = None

    book_data = {
        'id': book['id'],
        'title': book['title'],
        'author': book['author'],
        'coverUrl': cover_url,
        'audioUrl': url_for('static', filename='audio/' + book['audio_filename']) if book['audio_filename'] else None,
        'transcript': book['transcript'],
        'custom_summary': book['custom_summary'],
        "pdfUrl": pdf_url,
        "toc": book['toc'] if book['toc'] else "",
        "is_editor": is_editor,
        "user_plan": session.get('plan', 'basic')  # Pass user plan for AI Assistant restriction
    }

    return render_template("read_book.html", book=book, book_data=book_data, is_editor=is_editor)

@app.route("/api/books/<int:book_id>/update_content", methods=["POST"])
@login_required
def update_book_content(book_id):
    """API endpoint to update book summary and TOC (Publisher/Admin only)."""
    data = request.json
    custom_summary = data.get('custom_summary')
    toc = data.get('toc')

    conn = get_conn()
    conn.row_factory = sqlite3.Row
    book = conn.execute('SELECT uploader_id FROM books WHERE id = ?', (book_id,)).fetchone()

    if not book:
        conn.close()
        return jsonify({"success": False, "error": "Book not found"}), 404

    user_id = session.get('user_id')
    user_role = session.get('role')
    if user_id != book['uploader_id'] and user_role != 'admin':
        conn.close()
        return jsonify({"success": False, "error": "Unauthorized"}), 403

    try:
        if toc is not None and not isinstance(toc, str):
            import json
            toc = json.dumps(toc)

        conn.execute('UPDATE books SET custom_summary = ?, toc = ? WHERE id = ?', 
                     (custom_summary, toc, book_id))
        conn.commit()
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 500

    conn.close()
    return jsonify({"success": True})


# ---------- AI Summary Endpoint ----------
@app.route('/ai_summary', methods=['POST'])
@admin_required
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


@app.route("/community/reviews")
def community_reviews():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    conn = get_conn()
    c = conn.cursor()
    
    # Ensure manga_reviews table and columns exist (lazy migration)
    c.execute("""
        CREATE TABLE IF NOT EXISTS manga_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            manga_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            chapter_id INTEGER,
            content TEXT NOT NULL,
            rating INTEGER DEFAULT 5,
            has_spoilers BOOLEAN DEFAULT 0,
            status TEXT DEFAULT 'Reading',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (manga_id) REFERENCES books(id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (chapter_id) REFERENCES chapters(id),
            UNIQUE(manga_id, user_id)
        )
    """)
    for col, col_type in [("chapter_id", "INTEGER"), ("has_spoilers", "BOOLEAN DEFAULT 0"), ("status", "TEXT DEFAULT 'Reading'")]:
        try:
            c.execute(f"ALTER TABLE manga_reviews ADD COLUMN {col} {col_type}")
        except:
            pass
    conn.commit()
    
    manga_id_filter = request.args.get('manga_id', type=int)

    # 1. Fetch all reviews with user and book info
    # Book Reviews
    book_query = """
        SELECT r.id, r.user_id, r.book_id, r.rating, r.content, r.created_at, r.has_spoilers, r.status,
               u.username, u.avatar_url,
               b.title, b.cover_path, b.book_type, b.category,
               NULL as chapter_num
        FROM reviews r
        JOIN users u ON u.id = r.user_id
        JOIN books b ON b.id = r.book_id
    """
    if manga_id_filter:
        book_query += " WHERE b.id = ?"
        c.execute(book_query, (manga_id_filter,))
    else:
        c.execute(book_query)
        
    book_reviews = c.fetchall()

    # Manga Reviews
    manga_query = """
        SELECT mr.id, mr.user_id, mr.manga_id, mr.rating, mr.content, mr.created_at, mr.has_spoilers, mr.status,
               u.username, u.avatar_url,
               b.title, b.cover_path, b.book_type, b.category,
               ch.chapter_num
        FROM manga_reviews mr
        JOIN users u ON u.id = mr.user_id
        JOIN books b ON b.id = mr.manga_id
        LEFT JOIN chapters ch ON mr.chapter_id = ch.id
    """
    if manga_id_filter:
        manga_query += " WHERE b.id = ?"
        c.execute(manga_query, (manga_id_filter,))
    else:
        c.execute(manga_query)
        
    manga_reviews = c.fetchall()

    # Combine and sort by created_at DESC
    # We prefix manga IDs with 'm_' and book IDs with 'b_' to avoid collisions in the combined list
    # and to help the like/comment APIs later if we want to fix them.
    # Actually, for now let's just combine them.
    
    combined_raw = []
    for r in book_reviews:
        combined_raw.append(list(r) + ['book'])
    for r in manga_reviews:
        combined_raw.append(list(r) + ['manga'])

    # Sort DESC by created_at (index 5)
    combined_raw.sort(key=lambda x: x[5], reverse=True)
    
    reviews_raw = combined_raw
    
    reviews = []
    for row in reviews_raw:
        review_id = row[0]
        review_type = row[15]
        
        # 2. Fetch likes count and if current user liked it
        # Note: We current only have likes tables for 'book' reviews.
        # For manga reviews, we'll default to 0 for now unless we add tables.
        likes_count = 0
        is_liked = False
        
        if review_type == 'book':
            c.execute("SELECT COUNT(*) FROM review_likes WHERE review_id = ?", (review_id,))
            likes_count = c.fetchone()[0]
            if session.get('user_id'):
                c.execute("SELECT 1 FROM review_likes WHERE review_id = ? AND user_id = ?", (review_id, session['user_id']))
                is_liked = c.fetchone() is not None
        
        # 3. Fetch comments
        comments_list = []
        if review_type == 'book':
            c.execute("""
                SELECT rc.id, rc.user_id, rc.content, rc.created_at, rc.parent_id,
                       u.username, u.avatar_url
                FROM review_comments rc
                JOIN users u ON u.id = rc.user_id
                WHERE rc.review_id = ?
                ORDER BY rc.created_at ASC
            """, (review_id,))
            comments_raw = c.fetchall()
            
            # Organize comments and replies
            comments_map = {}
            for c_row in comments_raw:
                c_id = c_row[0]
                comment_obj = {
                    'id': str(c_id),
                    'userId': str(c_row[1]),
                    'user': {
                        'id': str(c_row[1]),
                        'username': c_row[5],
                        'avatarUrl': c_row[6] or 'https://picsum.photos/seed/you/100/100'
                    },
                    'body': c_row[2],
                    'createdAt': c_row[3],
                    'parent_id': c_row[4],
                    'likesCount': 0,
                    'isLiked': False,
                    'replies': []
                }
                
                # Fetch likes for comment
                c.execute("SELECT COUNT(*) FROM comment_likes WHERE comment_id = ?", (c_id,))
                comment_obj['likesCount'] = c.fetchone()[0]
                
                user_id = session.get('user_id')
                if user_id:
                    c.execute("SELECT 1 FROM comment_likes WHERE comment_id = ? AND user_id = ?", (c_id, user_id))
                    comment_obj['isLiked'] = c.fetchone() is not None
                
                comments_map[c_id] = comment_obj
                
            for c_id, c_obj in comments_map.items():
                parent_id = c_obj['parent_id']
                if parent_id and parent_id in comments_map:
                    comments_map[parent_id]['replies'].append(c_obj)
                else:
                    comments_list.append(c_obj)
        
        tags = [tag.strip() for tag in row[13].split(',')] if row[13] else []
        
        reviews.append({
            'id': f"{review_type}_{review_id}",
            'raw_id': review_id,
            'type': review_type,
            'userId': str(row[1]),
            'user': {
                'id': str(row[1]),
                'username': row[8],
                'avatarUrl': row[9] or 'https://picsum.photos/seed/you/100/100'
            },
            'media': {
                'id': str(row[2]),
                'title': row[10],
                'coverUrl': (f"/static/{row[11]}" if row[11] and not row[11].startswith(('http', 'https')) else (row[11] or 'https://picsum.photos/seed/cs/200/300')),
                'type': (row[12] or 'BOOK').upper(),
                'tags': tags,
                'chapter_num': row[14]
            },
            'rating': float(row[3]) if row[3] else 0.0,
            'body': row[4],
            'createdAt': row[5],
            'hasSpoilers': bool(row[6]),
            'status': row[7] or 'Reading',
            'likesCount': likes_count,
            'isLiked': is_liked,
            'comments': comments_list
        })
    
    conn.close()
    
    return render_template(
        "community_reviews.html",
        user_id=session.get("user_id"),
        username=session.get("username"),
        user_role=session.get("role"),
        user_plan=session.get("plan", "basic"),
        user_avatar=session.get("avatar_url"),
        initial_reviews=reviews,
        page_endpoint="community_reviews"
    )


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
@admin_required
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
@admin_required
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
@admin_required
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
@admin_required
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

        request_id = request.args.get('request_id')
        request_data = None
        if request_id:
            try:
                conn = get_conn()
                c = conn.cursor()
                c.execute("SELECT id, title, author, item_type FROM requests WHERE id = ?", (request_id,))
                row = c.fetchone()
                if row:
                    request_data = {
                        'id': row[0],
                        'title': row[1],
                        'author': row[2],
                        'type': row[3]
                    }
                conn.close()
            except Exception:
                pass
        return render_template("add_book.html", request_data=request_data)

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

        # Metadata
        transcript = (request.form.get("transcript") or "").strip()
        toc = (request.form.get("toc") or "").strip()
        custom_summary = (request.form.get("custom_summary") or "").strip()

        conn = get_conn()
        c = conn.cursor()
        # record uploader_id so the user who created the book can edit it later
        uploader_id = session.get('user_id')
        c.execute("""
        INSERT INTO books (title, author, category, pdf_filename, audio_filename, cover_path, book_type, uploader_id, description, transcript, toc, custom_summary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (title, author, category, pdf_filename, audio_filename, cover_path, book_type, uploader_id, (request.form.get("description") or ""), transcript, toc, custom_summary))
        conn.commit()
        conn.close()

        # Log book upload
        uploader_id = session.get("user_id")
        log_system_event('INFO', 'upload', f'User uploaded book: {title}', uploader_id, {'book_id': c.lastrowid, 'book_type': 'book'})
        
        # Sync community groups to create group for new book/genres
        sync_community_groups()
        
        # Fulfill Request if exists
        request_id = request.form.get("request_id")
        earned_amount = 0.0
        if request_id:
             try:
                 conn = get_conn()
                 # Get vote count logic
                 cur = conn.cursor()
                 cur.execute("SELECT vote_count FROM requests WHERE id=?", (request_id,))
                 row = cur.fetchone()
                 votes = row[0] if row else 0
                 
                 # Calc reward: $0.5 base + $0.2 per 2 votes
                 base_reward = 0.50
                 bonus = (votes // 2) * 0.20
                 earned_amount = base_reward + bonus
                 
                 # Update status
                 conn.execute("UPDATE requests SET status='Added' WHERE id=?", (request_id,))
                 
                 # Record earning
                 conn.execute("INSERT INTO publisher_earnings (user_id, request_id, amount, reason) VALUES (?, ?, ?, ?)", 
                              (session['user_id'], request_id, earned_amount, f"Filled request {request_id} (Votes: {votes})"))
                 
                 conn.commit()
                 conn.close()
             except:
                 pass
 
        if earned_amount > 0:
            flash(f"Book published! You earned ${earned_amount:.2f} for fulfilling this request.", "success")
        else:
            flash("Book published successfully.", "success")
        return redirect(url_for("home", earned=earned_amount if earned_amount > 0 else None))

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
                    # Create directory to save PDF and Images
                    chapter_dir = os.path.join(UPLOAD_FOLDER_MANGA, f"manga_{manga_id}_ch1")
                    os.makedirs(chapter_dir, exist_ok=True)
                    
                    pdf_path = os.path.join(chapter_dir, pdf_filename)
                    chapter_pdf.save(pdf_path)
                    
                    # Convert PDF to Images
                    try:
                        from pdf2image import convert_from_path
                        # Poppler path for Windows if standalone, or assume in PATH
                        # If on Windows and poppler not in PATH, this might fail unless configured.
                        # Assuming environment is set up as 'pdf2image' import exists.
                        images = convert_from_path(pdf_path)
                        
                        page_files = []
                        for i, image in enumerate(images):
                            page_filename = f"page_{i+1:03d}.jpg"
                            page_path = os.path.join(chapter_dir, page_filename)
                            image.save(page_path, "JPEG")
                            page_files.append(page_filename)
                            
                        if page_files:
                            pages_data = ",".join(page_files)
                            page_count = len(page_files)
                        else:
                            # Fallback if no images extracted (empty PDF?)
                             pages_data = pdf_filename
                             page_count = 1
                             
                    except Exception as e:
                        print(f"PDF Conversion Error: {e}")
                        # Fallback to just storing PDF (though reader might fail)
                        pages_data = pdf_filename
                        page_count = 1
                        flash(f"Warning: PDF saved but image conversion failed: {str(e)}", "warning")
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
            
            # Reward publisher 0.15$ for Chapter 1
            try:
                c.execute("""
                    INSERT INTO publisher_earnings (user_id, request_id, amount, reason)
                    VALUES (?, ?, ?, ?)
                """, (session['user_id'], None, 0.15, f"Chapter Upload Reward: {title} Ch 1"))
            except Exception as e:
                print(f"Error rewarding publisher for Ch 1: {e}")
            conn.commit()

        conn.close()

        # Log manga upload
        uploader_id = session.get("user_id")
        log_system_event('INFO', 'upload', f'User uploaded manga: {title} with {page_count} pages in Chapter 1', uploader_id, {'manga_id': manga_id, 'book_type': 'manga', 'chapters': 1, 'pages': page_count})

        # Sync community groups to create group for new manga/genres
        sync_community_groups()

        # Fulfill Request if exists
        request_id = request.form.get("request_id")
        earned_amount = 0.0
        if request_id:
             try:
                 conn = get_conn()
                 # Get vote count
                 cur = conn.cursor()
                 cur.execute("SELECT vote_count FROM requests WHERE id=?", (request_id,))
                 row = cur.fetchone()
                 votes = row[0] if row else 0
                 
                 # Calc reward
                 base_reward = 0.50
                 bonus = (votes // 2) * 0.20
                 earned_amount = base_reward + bonus
                 pass
                 
                 conn.execute("UPDATE requests SET status='Added', fulfilled_by=? WHERE id=?", (session['user_id'], request_id))
                 
                 # Record earning
                 conn.execute("INSERT INTO publisher_earnings (user_id, request_id, amount, reason) VALUES (?, ?, ?, ?)", 
                              (session['user_id'], request_id, earned_amount, f"Filled request {request_id} (Votes: {votes})"))
                 
                 conn.commit()
                 conn.close()
             except:
                 pass

        if earned_amount > 0:
            flash(f"Manga created! You earned ${earned_amount:.2f} for fulfilling this request.", "success")
        else:
            flash(f"Manga series created successfully with {page_count} pages in Chapter 1. You can add more chapters anytime.", "success")
            
        return redirect(url_for("manga", earned=earned_amount if earned_amount > 0 else None))


# ---------- Edit / Delete Book ----------
@app.route("/book/<int:id>/edit", methods=["GET", "POST"])
@admin_required
def edit_book(id):
    try:
        if "user_id" not in session:
            return redirect(url_for("login"))

        conn = get_conn()
        c = conn.cursor()

        # pull everything we need, including description and uploader
        c.execute("""
            SELECT id, title, author, category, description,
                   pdf_filename, audio_filename, cover_path, uploader_id, book_type,
                   transcript, toc, custom_summary
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
            "transcript": row[10],
            "toc": row[11],
            "custom_summary": row[12],
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
            custom_summary = (request.form.get('custom_summary') or '').strip()
            transcript = (request.form.get('transcript') or '').strip()
            toc = (request.form.get('toc') or '').strip()

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
                       cover_path = ?,
                       transcript = ?,
                       toc = ?,
                       custom_summary = ?
                 WHERE id = ?
            """, (title, author, category, description, pdf_filename, audio_filename, cover_path, transcript, toc, custom_summary, id))

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
@admin_required
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
        SELECT books.title, books.category, history.date_read, books.author, books.cover_path, books.id
        FROM history
        JOIN books ON history.book_id = books.id
        WHERE history.user_id = ?
        ORDER BY history.date_read DESC
        LIMIT 50
    """, (user_id,))
    hist = c.fetchall()

    # Get currently reading from watchlist
    c.execute("""
        SELECT b.title, b.author, b.cover_path, w.progress, b.id
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
        {"id": r[4], "title": r[0], "author": r[1], "progress": r[3] or 0, "cover": r[2]}
        for r in currently_reading_raw
    ]

    # Format recent finished (first 6 from history)
    recent_finished = [
        {"id": r[5], "title": r[0], "author": r[3], "cover": r[4]}
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
        plan=session.get("plan", "basic"),
        role=session.get("role", "member"),
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

    # Fetch avatar settings for the VIEWED user
    profile_avatar_settings = fetch_user_avatar_settings(user_id)

    return render_template(
        "user_profile.html",
        user=user,
        read_count=read_count,
        watchlist_stats=watchlist_stats,
        fav_count=fav_count,
        recent_activity=recent_activity,
        profile_avatar_settings=profile_avatar_settings
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

            # Handle Profile Picture Upload
            if "avatar" in request.files:
                file = request.files["avatar"]
                if file and file.filename != "" and allowed_file(file.filename):
                    filename = secure_filename(f"user_{user_id}_{file.filename}")
                    filepath = os.path.join(UPLOAD_FOLDER, filename)
                    file.save(filepath)
                    
                    # Store as relative path for template use
                    avatar_url = f"uploads/avatars/{filename}"
                    c.execute("UPDATE users SET avatar_url=? WHERE id=?", (avatar_url, user_id))

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
    c.execute("SELECT username, email, avatar_url FROM users WHERE id=?", (user_id,))
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


# ---------- Reading History ----------
@app.route("/reading_history")
def reading_history():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        SELECT b.id, b.title, b.author, b.cover_path, h.date_read
        FROM history h
        JOIN books b ON h.book_id = b.id
        WHERE h.user_id = ?
        ORDER BY h.date_read DESC
    """, (user_id,))
    history_data = c.fetchall()
    conn.close()

    formatted_history = []
    for row in history_data:
        # Format date if needed, or pass raw
        formatted_history.append({
            "book_id": row[0],
            "title": row[1],
            "author": row[2],
            "cover": row[3],
            "date_read": row[4]
        })

    return render_template("reading_history.html", history=formatted_history)

# ---------- Watchlist ----------
@app.route("/watchlist")
@admin_required
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
@admin_required
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
@admin_required
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
@admin_required
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
@login_required
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
@login_required
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
               f.created_at, b.book_type
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
               h.date_read, b.book_type
        FROM history h
        JOIN books b ON b.id = h.book_id
        WHERE h.user_id = ?
        ORDER BY h.date_read DESC
        LIMIT 20
    """, (session["user_id"],)).fetchall()
    
    conn.close()

    # Format data for template
    favorite_books_formatted = []
    for r in favorite_books:
        book_id, title, author, category, pdf, audio, cover_path, date_added, book_type = r
        
        # Handle cover image path
        if cover_path:
            if cover_path.startswith(('http://', 'https://')):
                image_url = cover_path
            else:
                image_url = f"/static/{cover_path}"
        else:
            image_url = f"https://picsum.photos/seed/{book_id}/400/600"
            
        favorite_books_formatted.append({
            "id": book_id, 
            "title": title, 
            "author": author, 
            "category": category, 
            "cover": image_url,
            "date_added": date_added,
            "type": book_type
        })
    
    recently_read_books = []
    for r in recently_read:
        b_id, b_title, b_author, b_cat, b_pdf, b_audio, b_cover, b_date, b_type = r
        if b_cover:
            img_url = b_cover if b_cover.startswith(('http://', 'https://')) else f"/static/{b_cover}"
        else:
            img_url = f"https://picsum.photos/seed/{b_id}/400/600"
            
        recently_read_books.append({
            "id": b_id, 
            "title": b_title, 
            "author": b_author, 
            "category": b_cat, 
            "cover": img_url, 
            "date_read": b_date,
            "type": b_type
        })
    
    return render_template("favorites.html", 
                         favorite_books=favorite_books_formatted, 
                         categories=categories,
                         recently_read_books=recently_read_books)


@app.post("/favorites/add")
@login_required
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
@login_required
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
@login_required
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


@app.post("/api/favorites/toggle")
@login_required
def api_favorites_toggle():
    """Toggle favorite status for a book via AJAX"""
    data    = request.get_json() or {}
    book_id = data.get("book_id")
    
    if not book_id:
        return jsonify({"success": False, "error": "Missing book_id"}), 400
        
    user_id = session["user_id"]
    conn = get_conn()
    c = conn.cursor()
    
    try:
        # Check if book exists
        c.execute("SELECT title FROM books WHERE id = ?", (book_id,))
        book = c.fetchone()
        if not book:
            conn.close()
            return jsonify({"success": False, "error": "Book not found"}), 404
            
        book_title = book[0]
        
        # Check if already favorited
        c.execute("SELECT 1 FROM favorites WHERE user_id = ? AND book_id = ?", (user_id, book_id))
        is_favorite = c.fetchone() is not None
        
        if is_favorite:
            # Remove from favorites
            c.execute("DELETE FROM favorites WHERE user_id = ? AND book_id = ?", (user_id, book_id))
            status = "removed"
            message = f"Removed '{book_title}' from favorites"
        else:
            # Add to favorites
            c.execute("INSERT INTO favorites (user_id, book_id) VALUES (?, ?)", (user_id, book_id))
            status = "added"
            message = f"Added '{book_title}' to favorites"
            
            # Log activity
            try:
                c.execute("""
                    INSERT INTO activity_log (user_id, book_id, activity_type)
                    VALUES (?, ?, ?)
                """, (user_id, book_id, 'favorited'))
            except Exception:
                pass
                
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True, 
            "status": status, 
            "message": message,
            "book_id": book_id
        })
        
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/manga")
@login_required
def manga():
    try:
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
        """)
        raw_cats = [row[0] for row in c.fetchall()]
        categories_set = set()
        for rc in raw_cats:
            for cat in rc.split(','):
                 cleaned = cat.strip()
                 if cleaned:
                     categories_set.add(cleaned)
        categories = sorted(list(categories_set))

        # Updated query with chapter count
        base_sql = """
            SELECT b.id, b.title, b.author, COALESCE(b.category,'General') AS category,
                   b.pdf_filename, b.audio_filename, b.cover_path,
                   COUNT(ch.id) as chapter_count
            FROM books b
            LEFT JOIN chapters ch ON b.id = ch.manga_id
            WHERE COALESCE(b.book_type,'book')='manga'
        """
        params = []

        if selected:
            base_sql += " AND ',' || REPLACE(COALESCE(b.category,'General'), ' ', '') || ',' LIKE ?"
            params.append(f"%,{selected.replace(' ', '')},%")

        if q:
            base_sql += " AND (b.title LIKE ? OR b.author LIKE ?)"
            search_term = f"%{q}%"
            params.extend([search_term, search_term])

        base_sql += " GROUP BY b.id ORDER BY datetime(b.created_at) DESC"

        c.execute(base_sql, params)
        mangas = c.fetchall()

        # Fetch Continue Reading for logged-in user
        continue_reading = []
        if session.get("user_id"):
            uid = session["user_id"]
            c.execute("""
                SELECT b.id, b.title, b.cover_path, rh.chapter_id, rh.page_index, c.chapter_num
                FROM reading_history rh
                JOIN books b ON rh.manga_id = b.id
                JOIN chapters c ON rh.chapter_id = c.id
                WHERE rh.user_id = ?
                ORDER BY rh.updated_at DESC
                LIMIT 5
            """, (uid,))
            continue_reading = c.fetchall()

        conn.close()

        return render_template(
            "manga.html",
            mangas=mangas,
            categories=categories,
            selected_category=selected,
            q=q,
            body_class="manga-theme",
            continue_reading=continue_reading
        )

    except Exception as e:
        logger.error(f"Error in manga route: {e}\n{traceback.format_exc()}")
        flash("An error occurred while loading the manga library.", "danger")
        try:
            if 'conn' in locals() and conn:
                conn.close()
        except:
            pass
        return redirect(url_for("home"))



# ---------- Manga Detail Page ----------
@app.route("/manga/detail/<int:id>")
@login_required
def manga_detail(id):
    """Display detailed view of a manga series."""
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_conn()
    c = conn.cursor()

    # Fetch manga details with extended info and uploader
    c.execute("""
        SELECT b.id, b.title, b.author, COALESCE(b.category,'General') AS category,
               b.pdf_filename, b.audio_filename, b.cover_path, b.description,
               u.username as publisher_name
        FROM books b
        LEFT JOIN users u ON b.uploader_id = u.id
        WHERE b.id = ? AND COALESCE(b.book_type,'book')='manga'
    """, (id,))
    manga = c.fetchone()

    if not manga:
        conn.close()
        flash("Manga not found.", "danger")
        return redirect(url_for("manga"))

    # Get chapter count
    c.execute("SELECT COUNT(*) FROM chapters WHERE manga_id = ?", (id,))
    chapter_count = c.fetchone()[0]

    # Get average rating
    c.execute("""
        SELECT AVG(rating) FROM reviews WHERE book_id = ?
    """, (id,))
    avg_rating_row = c.fetchone()
    avg_rating = avg_rating_row[0] if avg_rating_row and avg_rating_row[0] else None

    # Get recommendations (same category, excluding current)
    categories = manga[3].split(',') if manga[3] else []
    first_category = categories[0].strip() if categories else 'General'
    
    c.execute("""
        SELECT b.id, b.title, b.author, COALESCE(b.category,'General'),
               b.pdf_filename, b.audio_filename, b.cover_path,
               (SELECT COUNT(*) FROM chapters WHERE manga_id = b.id) as chapter_count
        FROM books b
        WHERE COALESCE(b.book_type,'book')='manga'
          AND b.id != ?
          AND b.category LIKE ?
        ORDER BY datetime(b.created_at) DESC
        LIMIT 10
    """, (id, f"%{first_category}%"))
    recommendations = c.fetchall()

    # Get most popular manga (by view count from manga_progress)
    c.execute("""
        SELECT b.id, b.title, b.author, COALESCE(b.category,'General'),
               b.pdf_filename, b.audio_filename, b.cover_path,
               (SELECT COUNT(*) FROM chapters WHERE manga_id = b.id) as chapter_count,
               (SELECT COUNT(*) FROM manga_progress WHERE manga_id = b.id) as view_count,
               (SELECT COUNT(*) FROM favorites WHERE book_id = b.id) as fav_count
        FROM books b
        WHERE COALESCE(b.book_type,'book')='manga'
        ORDER BY view_count DESC, fav_count DESC
        LIMIT 5
    """)
    popular_manga = c.fetchall()

    conn.close()

    return render_template(
        "manga_detail.html",
        manga=manga,
        chapter_count=chapter_count,
        avg_rating=avg_rating,
        recommendations=recommendations,
        popular_manga=popular_manga
    )


@app.route("/api/manga/record_view", methods=["POST"])
def record_manga_view():
    """Record a view after 15 seconds of engagement."""
    if not session.get("user_id"):
        return jsonify({"success": False, "error": "Login required"}), 401
    
    data = request.json
    uid = session["user_id"]
    manga_id = data.get("manga_id")
    chapter_id = data.get("chapter_id")

    if not manga_id or not chapter_id:
        return jsonify({"success": False, "error": "Missing manga_id or chapter_id"}), 400

    conn = get_conn()
    c = conn.cursor()
    try:
        # We use manga_progress as the source for view counts in the ranking query.
        # This INSERT OR IGNORE / REPLACE logic ensures 1 view per user per manga.
        # If we want to allow re-views, we'd need a different schema, 
        # but for ranking, unique viewers is usually better.
        c.execute("""
            INSERT INTO manga_progress (user_id, manga_id, chapter_id, updated_at)
            VALUES (?, ?, ?, datetime('now'))
            ON CONFLICT(user_id, manga_id) DO UPDATE SET
                chapter_id = excluded.chapter_id,
                updated_at = excluded.updated_at
        """, (uid, manga_id, chapter_id))
        conn.commit()
        
        # Also log this as an activity
        c.execute("""
            INSERT INTO activity_log (user_id, book_id, activity_type, timestamp)
            VALUES (?, ?, 'view_engaged', datetime('now'))
        """, (uid, manga_id))
        conn.commit()
        
        return jsonify({"success": True, "message": "Engaged view recorded"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        conn.close()


@app.route("/api/books/record_view", methods=["POST"])
def record_book_view():
    """Record a book view after 1 minute of engagement."""
    if not session.get("user_id"):
        return jsonify({"success": False, "error": "Login required"}), 401
    
    data = request.json
    uid = session["user_id"]
    book_id = data.get("book_id")

    if not book_id:
        return jsonify({"success": False, "error": "Missing book_id"}), 400

    conn = get_conn()
    c = conn.cursor()
    try:
        # For books, we use manga_progress as well since the ranking query joins on it.
        # We use a dummy chapter_id (e.g. 0 or -1) if it's not a manga with chapters.
        # The ranking query counts DISTINCT user_id per manga_id.
        c.execute("""
            INSERT INTO manga_progress (user_id, manga_id, chapter_id, updated_at)
            VALUES (?, ?, 0, datetime('now'))
            ON CONFLICT(user_id, manga_id) DO NOTHING
        """, (uid, book_id))
        conn.commit()
        
        # Also log this as an activity
        c.execute("""
            INSERT INTO activity_log (user_id, book_id, activity_type, timestamp)
            VALUES (?, ?, 'book_view_engaged', datetime('now'))
        """, (uid, book_id))
        conn.commit()
        
        return jsonify({"success": True, "message": "Book view recorded"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        conn.close()


@app.route("/api/save_progress", methods=["POST"])
def save_reading_progress():
    if not session.get("user_id"):
        return jsonify({"success": False, "error": "Login required"}), 401
    
    data = request.json
    uid = session["user_id"]
    manga_id = data.get("manga_id")
    chapter_id = data.get("chapter_id")
    page_index = data.get("page_index")

    if not all([manga_id, chapter_id, page_index is not None]):
         return jsonify({"success": False, "error": "Missing data"}), 400

    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute("""
            INSERT INTO reading_history (user_id, manga_id, chapter_id, page_index, updated_at)
            VALUES (?, ?, ?, ?, datetime('now'))
            ON CONFLICT(user_id, manga_id) DO UPDATE SET
                chapter_id = excluded.chapter_id,
                page_index = excluded.page_index,
                updated_at = excluded.updated_at
        """, (uid, manga_id, chapter_id, page_index))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        conn.close()


@app.route("/manga/read/<int:id>")
@login_required
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
        "manga_reader.html",
        manga=manga,
        chapters=chapters,
        related_manga=related_manga,
        chapter=chapters[0] if chapters else None
    )


# ---------- Modern Manga Reader (v2) ----------
@app.route("/manga/<int:id>")
@login_required
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
        "manga_reader.html",
        manga=manga,
        chapters=chapters,
        chapter=chapters[0] if chapters else None
    )


# ---------- Chapter Pages API ----------
@app.route("/api/chapter/<int:chapter_id>/pages")
def get_chapter_pages(chapter_id):
    """Get all pages for a specific chapter."""
    try:
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
            return jsonify({"error": "Chapter not found"}), 404
        
        chapter_id, manga_id, chapter_num, pdf_filename, page_count = chapter
        
        if not pdf_filename:
            return jsonify([])
        
        pages = []
        
        # Check if it's a PDF file (single file) or comma-separated images
        if pdf_filename.lower().endswith('.pdf'):
            # It's a PDF file - for now, just return the PDF path
            # The frontend will need to handle PDF rendering
            chapter_dir = f"manga_{manga_id}_ch{chapter_num}"
            pages.append({
                "page_num": 1,
                "url": f"/static/manga/{chapter_dir}/{pdf_filename}",
                "type": "pdf"
            })
        else:
            # It's comma-separated image filenames
            page_files = [p.strip() for p in pdf_filename.split(',') if p.strip()]
            chapter_dir = f"manga_{manga_id}_ch{chapter_num}"
            
            for idx, filename in enumerate(page_files, 1):
                pages.append({
                    "page_num": idx,
                    "url": f"/static/manga/{chapter_dir}/{filename}",
                    "type": "image"
                })
        
        return jsonify(pages)
    except Exception as e:
        print(f"Error getting chapter pages: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/manga/chat", methods=["POST"])
def manga_chat_api():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    # Check plan
    user_plan = session.get('plan', 'basic')
    if user_plan not in ['pro', 'ultimate']:
        return jsonify({"error": "Pro plan required for AI Chatbot"}), 403
    
    data = request.json
    user_msg = data.get('message')
    manga_id = data.get('manga_id')
    chapter_num = data.get('chapter_num')
    
    if not user_msg:
        return jsonify({"error": "No message provided"}), 400

    # Fetch context
    context_text = f"User is reading Manga ID {manga_id}, Chapter {chapter_num}."
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT title, author, description FROM books WHERE id=?", (manga_id,))
        m_row = c.fetchone()
        if m_row:
            context_text += f" Manga Title: {m_row[0]}. Author: {m_row[1]}. Description: {m_row[2]}."
        
        c.execute("SELECT title FROM chapters WHERE manga_id=? AND chapter_num=?", (manga_id, chapter_num))
        c_row = c.fetchone()
        if c_row:
            context_text += f" Chapter Title: {c_row[0]}."
        conn.close()
    except:
        pass

    try:
        ai = ImageSummaryAI()
        response_text = ai.chat_with_context(user_msg, context_text)
        return jsonify({"success": True, "reply": response_text})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/manga/search")
def search_manga_api():
    """API for manga search/autocompletion"""
    query = request.args.get('q', '').strip()
    
    conn = get_conn()
    c = conn.cursor()
    
    if not query:
        # Return mostly recent or popular mangas if no query
        c.execute("""
            SELECT id, title, author, cover_path, category
            FROM books 
            WHERE COALESCE(book_type,'book')='manga'
            ORDER BY created_at DESC
            LIMIT 10
        """)
    else:
        c.execute("""
            SELECT id, title, author, cover_path, category
            FROM books 
            WHERE (title LIKE ? OR author LIKE ?) AND COALESCE(book_type,'book')='manga'
            LIMIT 10
        """, (f'%{query}%', f'%{query}%'))
    
    results = []
    for row in c.fetchall():
        cover = row[3]
        # Normalize cover path
        if cover and not cover.startswith('http') and not cover.startswith('/'):
            cover = f'/static/{cover}'
        elif not cover:
            cover = None 
            
        results.append({
            'id': row[0],
            'title': row[1],
            'author': row[2],
            'cover': cover,
            'category': row[4]
        })

    conn.close()
    return jsonify(results)


@app.route("/api/manga/<int:manga_id>/summary", methods=["GET"])
def get_manga_summary(manga_id):
    """Get or generate AI summary for a manga."""
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    # Check plan
    user_plan = session.get('plan', 'basic')
    if user_plan not in ['pro', 'ultimate']:
        return jsonify({"error": "Pro plan required for AI Assistant"}), 403
    
    try:
        conn = get_conn()
        c = conn.cursor()
        
        # Check cache
        c.execute("SELECT summary FROM ai_summaries WHERE item_type='manga' AND item_id=?", (manga_id,))
        row = c.fetchone()
        
        if row:
            conn.close()
            return jsonify({"success": True, "summary": row[0], "cached": True})
        
        # Generate new summary
        c.execute("SELECT title, description FROM books WHERE id=?", (manga_id,))
        m_row = c.fetchone()
        if not m_row:
            conn.close()
            return jsonify({"error": "Manga not found"}), 404
        
        title, description = m_row
        if not description:
            conn.close()
            return jsonify({"success": True, "summary": "No description available for this manga."})
            
        ai = ImageSummaryAI()
        summary = ai.chat_with_context(f"Summarize this manga titled '{title}': {description}", "You are a helpful manga assistant.")
        
        # Cache summary
        c.execute("INSERT OR REPLACE INTO ai_summaries (item_type, item_id, summary, created_at) VALUES ('manga', ?, ?, ?)",
                  (manga_id, summary, datetime.utcnow().isoformat()))
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "summary": summary, "cached": False})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/manga/page/analyze", methods=["POST"])
def analyze_manga_page():
    """Deep AI analysis for a specific manga page."""
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    # Check plan
    user_plan = session.get('plan', 'basic')
    if user_plan != 'ultimate':
        return jsonify({"error": "Ultimate plan required for Scene Analysis"}), 403
        
    data = request.json
    page_url = data.get('page_url')
    
    if not page_url:
        return jsonify({"error": "No page URL provided"}), 400
        
    try:
        # Convert /static/manga/... to local file path
        if page_url.startswith('/static/'):
            # Path logic: remove leading / and join with APP_ROOT
            rel_path = page_url.lstrip('/')
            image_path = os.path.join(APP_ROOT, rel_path)
        else:
            return jsonify({"error": "Invalid image source"}), 400
            
        if not os.path.exists(image_path):
            return jsonify({"error": f"Image file not found at {image_path}"}), 404
            
        ai = ImageSummaryAI()
        analysis = ai.analyze_manga_scene(image_path)
        
        return jsonify({
            "success": True, 
            "analysis": analysis
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/manga/page/context", methods=["POST"])
def get_manga_page_context_api():
    """AI analysis for cultural and idiom context of a manga page."""
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    # Check plan
    user_plan = session.get('plan', 'basic')
    if user_plan != 'ultimate':
        return jsonify({"error": "Ultimate plan required for Culture & Context"}), 403
        
    data = request.json
    page_url = data.get('page_url')
    
    if not page_url:
        return jsonify({"error": "No page URL provided"}), 400
        
    try:
        if page_url.startswith('/static/'):
            rel_path = page_url.lstrip('/')
            image_path = os.path.join(APP_ROOT, rel_path)
        else:
            return jsonify({"error": "Invalid image source"}), 400
            
        if not os.path.exists(image_path):
            return jsonify({"error": "Image file not found"}), 404
            
        ai = ImageSummaryAI()
        context_data = ai.get_manga_page_context(image_path)
        
        return jsonify({
            "success": True, 
            "context": context_data
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/manga/mood", methods=["POST"])
def get_manga_mood():
    """Detect the mood of a manga page for ambient audio."""
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    # Check plan
    user_plan = session.get('plan', 'basic')
    if user_plan != 'ultimate':
        return jsonify({"error": "Ultimate plan required for AI Ambient OST"}), 403
        
    data = request.json
    page_url = data.get('page_url')
    
    if not page_url:
        return jsonify({"error": "No page URL provided"}), 400
        
    try:
        if page_url.startswith('/static/'):
            rel_path = page_url.lstrip('/')
            image_path = os.path.join(APP_ROOT, rel_path)
        else:
            return jsonify({"error": "Invalid image source"}), 400
            
        if not os.path.exists(image_path):
            return jsonify({"error": "Image file not found"}), 404
            
        ai = ImageSummaryAI()
        mood = ai.detect_manga_mood(image_path)
        
        return jsonify({
            "success": True, 
            "mood": mood
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ---------- Manga Comments API ----------
@app.route("/api/manga/<int:manga_id>/comments", methods=["GET"])
def get_manga_comments(manga_id):
    """Get comments for a manga."""
    try:
        conn = get_conn()
        c = conn.cursor()
        
        # Ensure table exists
        c.execute("""
            CREATE TABLE IF NOT EXISTS manga_comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                manga_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                likes INTEGER DEFAULT 0,
                parent_id INTEGER DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (manga_id) REFERENCES books(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        user_id = session.get("user_id")
        
        c.execute("""
            SELECT mc.id, mc.content, mc.created_at, 
                   (SELECT COUNT(*) FROM manga_comment_likes WHERE comment_id = mc.id) as likes_count,
                   u.username, u.avatar_url, mc.user_id, mc.parent_id,
                   EXISTS(SELECT 1 FROM manga_comment_likes WHERE comment_id = mc.id AND user_id = ?) as user_liked
            FROM manga_comments mc
            JOIN users u ON mc.user_id = u.id
            WHERE mc.manga_id = ?
            ORDER BY mc.created_at DESC
            LIMIT 50
        """, (user_id, manga_id))
        comments = c.fetchall()
        conn.close()
        
        return jsonify([{
            "id": comment[0],
            "content": comment[1],
            "created_at": comment[2],
            "likes": comment[3],
            "username": comment[4],
            "avatar": comment[5],
            "user_id": comment[6],
            "parent_id": comment[7],
            "user_liked": bool(comment[8])
        } for comment in comments])
    except Exception as e:
        print(f"Error getting comments: {e}")
        return jsonify([])


@app.route("/api/manga/<int:manga_id>/comments", methods=["POST"])
def post_manga_comment(manga_id):
    """Post a comment on a manga."""
    if "user_id" not in session:
        return jsonify({"error": "Please log in to comment"}), 401
    
    data = request.json
    content = data.get("content", "").strip()
    parent_id = data.get("parent_id")
    
    if not content:
        return jsonify({"error": "Comment cannot be empty"}), 400
    
    if len(content) > 1000:
        return jsonify({"error": "Comment too long (max 1000 characters)"}), 400
    
    try:
        conn = get_conn()
        c = conn.cursor()
        
        c.execute("""
            INSERT INTO manga_comments (manga_id, user_id, content, parent_id)
            VALUES (?, ?, ?, ?)
        """, (manga_id, session["user_id"], content, parent_id))
        conn.commit()
        conn.close()
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------- Comment Actions API ----------
@app.route("/api/comment/<int:comment_id>/like", methods=["POST"])
def like_comment(comment_id):
    """Toggle like on a comment (unique per user)."""
    if "user_id" not in session:
        return jsonify({"error": "Please log in to like comments"}), 401
    
    user_id = session["user_id"]
    try:
        conn = get_conn()
        c = conn.cursor()
        
        # Check if already liked
        c.execute("SELECT 1 FROM manga_comment_likes WHERE user_id = ? AND comment_id = ?", (user_id, comment_id))
        if c.fetchone():
            c.execute("DELETE FROM manga_comment_likes WHERE user_id = ? AND comment_id = ?", (user_id, comment_id))
            liked = False
        else:
            c.execute("INSERT INTO manga_comment_likes (user_id, comment_id) VALUES (?, ?)", (user_id, comment_id))
            liked = True
        
        conn.commit()
        
        c.execute("SELECT COUNT(*) FROM manga_comment_likes WHERE comment_id = ?", (comment_id,))
        count = c.fetchone()[0]
        conn.close()
        
        return jsonify({"likes": count, "liked": liked})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/chapter/<int:chapter_id>/rate", methods=["POST"])
def rate_chapter(chapter_id):
    """Rate a chapter (like/dislike)."""
    if "user_id" not in session:
        return jsonify({"error": "Please log in to rate chapters"}), 401
    
    user_id = session["user_id"]
    data = request.json
    rating = data.get("rating") # 1 for like, -1 for dislike, 0 to remove
    
    if rating not in [1, -1, 0]:
        return jsonify({"error": "Invalid rating"}), 400
        
    try:
        conn = get_conn()
        c = conn.cursor()
        
        if rating == 0:
            c.execute("DELETE FROM manga_chapter_ratings WHERE user_id = ? AND chapter_id = ?", (user_id, chapter_id))
        else:
            c.execute("""
                INSERT INTO manga_chapter_ratings (user_id, chapter_id, rating)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, chapter_id) DO UPDATE SET rating = excluded.rating
            """, (user_id, chapter_id, rating))
        
        conn.commit()
        
        # Get new counts
        c.execute("SELECT COUNT(*) FROM manga_chapter_ratings WHERE chapter_id = ? AND rating = 1", (chapter_id,))
        likes = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM manga_chapter_ratings WHERE chapter_id = ? AND rating = -1", (chapter_id,))
        dislikes = c.fetchone()[0]
        
        conn.close()
        return jsonify({"likes": likes, "dislikes": dislikes, "user_rating": rating})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/chapter/<int:chapter_id>/rating", methods=["GET"])
def get_chapter_rating(chapter_id):
    """Get rating counts and current user's rating for a chapter."""
    user_id = session.get("user_id")
    try:
        conn = get_conn()
        c = conn.cursor()
        
        c.execute("SELECT COUNT(*) FROM manga_chapter_ratings WHERE chapter_id = ? AND rating = 1", (chapter_id,))
        likes = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM manga_chapter_ratings WHERE chapter_id = ? AND rating = -1", (chapter_id,))
        dislikes = c.fetchone()[0]
        
        user_rating = 0
        if user_id:
            c.execute("SELECT rating FROM manga_chapter_ratings WHERE user_id = ? AND chapter_id = ?", (user_id, chapter_id))
            result = c.fetchone()
            if result:
                user_rating = result[0]
                
        conn.close()
        return jsonify({"likes": likes, "dislikes": dislikes, "user_rating": user_rating})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/comment/<int:comment_id>", methods=["PUT"])
def edit_comment(comment_id):
    """Edit a comment (owner only)."""
    if "user_id" not in session:
        return jsonify({"error": "Please log in to edit comments"}), 401
    
    data = request.json
    content = data.get("content", "").strip()
    
    if not content:
        return jsonify({"error": "Comment cannot be empty"}), 400
    
    try:
        conn = get_conn()
        c = conn.cursor()
        
        # Check ownership
        c.execute("SELECT user_id FROM manga_comments WHERE id = ?", (comment_id,))
        result = c.fetchone()
        
        if not result:
            conn.close()
            return jsonify({"error": "Comment not found"}), 404
        
        if result[0] != session["user_id"] and session.get("role") != "admin":
            conn.close()
            return jsonify({"error": "You can only edit your own comments"}), 403
        
        c.execute("UPDATE manga_comments SET content = ? WHERE id = ?", (content, comment_id))
        conn.commit()
        conn.close()
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/comment/<int:comment_id>", methods=["DELETE"])
def delete_comment(comment_id):
    """Delete a comment (owner or admin only)."""
    if "user_id" not in session:
        return jsonify({"error": "Please log in to delete comments"}), 401
    
    try:
        conn = get_conn()
        c = conn.cursor()
        
        # Check ownership
        c.execute("SELECT user_id FROM manga_comments WHERE id = ?", (comment_id,))
        result = c.fetchone()
        
        if not result:
            conn.close()
            return jsonify({"error": "Comment not found"}), 404
        
        if result[0] != session["user_id"] and session.get("role") != "admin":
            conn.close()
            return jsonify({"error": "You can only delete your own comments"}), 403
        
        c.execute("DELETE FROM manga_comments WHERE id = ?", (comment_id,))
        conn.commit()
        conn.close()
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------- Manga Reviews API ----------
@app.route("/api/manga/<int:manga_id>/reviews", methods=["GET"])
def get_manga_reviews(manga_id):
    """Get reviews for a manga."""
    try:
        conn = get_conn()
        c = conn.cursor()
        
        # Ensure table exists
        c.execute("""
            CREATE TABLE IF NOT EXISTS manga_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                manga_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                chapter_id INTEGER,
                content TEXT NOT NULL,
                rating INTEGER DEFAULT 5,
                has_spoilers BOOLEAN DEFAULT 0,
                status TEXT DEFAULT 'Reading',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (manga_id) REFERENCES books(id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (chapter_id) REFERENCES chapters(id),
                UNIQUE(manga_id, user_id)
            )
        """)
        
        # Add columns if they don't exist
        for col, col_type in [("chapter_id", "INTEGER"), ("has_spoilers", "BOOLEAN DEFAULT 0"), ("status", "TEXT DEFAULT 'Reading'")]:
            try:
                c.execute(f"ALTER TABLE manga_reviews ADD COLUMN {col} {col_type}")
            except:
                pass
            
        limit = request.args.get("limit", 20, type=int)
        
        c.execute("""
            SELECT mr.id, mr.content, mr.rating, mr.created_at,
                   u.username, u.avatar_url,
                   ch.chapter_num, mr.has_spoilers, mr.status
            FROM manga_reviews mr
            JOIN users u ON mr.user_id = u.id
            LEFT JOIN chapters ch ON mr.chapter_id = ch.id
            WHERE mr.manga_id = ?
            ORDER BY mr.created_at DESC
            LIMIT ?
        """, (manga_id, limit))
        reviews = c.fetchall()
        conn.close()
        
        return jsonify([{
            "id": review[0],
            "content": review[1],
            "rating": review[2],
            "created_at": review[3],
            "username": review[4],
            "avatar": review[5],
            "chapter_num": review[6],
            "has_spoilers": bool(review[7]),
            "status": review[8]
        } for review in reviews])
    except Exception as e:
        print(f"Error getting reviews: {e}")
        return jsonify([])

@app.route("/api/manga/<int:manga_id>/reviews", methods=["POST"])
def post_manga_review(manga_id):
    """Post a review on a manga."""
    if "user_id" not in session:
        return jsonify({"error": "Please log in to review"}), 401
    
    data = request.json
    content = data.get("content", "").strip()
    rating = data.get("rating", 5)
    
    if not content:
        return jsonify({"error": "Review cannot be empty"}), 400
    
    if not isinstance(rating, int) or rating < 1 or rating > 5:
        return jsonify({"error": "Rating must be 1-5"}), 400
    
    try:
        conn = get_conn()
        c = conn.cursor()
        
        # Ensure table exists
        c.execute("""
            CREATE TABLE IF NOT EXISTS manga_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                manga_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                chapter_id INTEGER,
                content TEXT NOT NULL,
                rating INTEGER DEFAULT 5,
                has_spoilers BOOLEAN DEFAULT 0,
                status TEXT DEFAULT 'Reading',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (manga_id) REFERENCES books(id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (chapter_id) REFERENCES chapters(id),
                UNIQUE(manga_id, user_id)
            )
        """)
        
        # Add columns if they don't exist
        for col, col_type in [("chapter_id", "INTEGER"), ("has_spoilers", "BOOLEAN DEFAULT 0"), ("status", "TEXT DEFAULT 'Reading'")]:
            try:
                c.execute(f"ALTER TABLE manga_reviews ADD COLUMN {col} {col_type}")
            except:
                pass

        chapter_id = data.get("chapter_id")
        has_spoilers = data.get("has_spoilers", False)
        status = data.get("status", "Reading")
        
        # Upsert - update if exists, insert if not
        c.execute("""
            INSERT INTO manga_reviews (manga_id, user_id, content, rating, chapter_id, has_spoilers, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(manga_id, user_id) DO UPDATE SET
                content = excluded.content,
                rating = excluded.rating,
                chapter_id = excluded.chapter_id,
                has_spoilers = excluded.has_spoilers,
                status = excluded.status,
                created_at = CURRENT_TIMESTAMP
        """, (manga_id, session["user_id"], content, rating, chapter_id, has_spoilers, status))
        conn.commit()
        conn.close()
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
        
        # Create chapter directory for images
        chapter_dir = os.path.join(UPLOAD_FOLDER_MANGA, f"manga_{manga_id}_ch{chapter_num}")
        os.makedirs(chapter_dir, exist_ok=True)
        
        pdf_filename = secure_filename(chapter_pdf.filename)
        pdf_path = os.path.join(chapter_dir, pdf_filename)
        chapter_pdf.save(pdf_path)
        
        # Convert PDF to Images
        try:
            from pdf2image import convert_from_path
            images = convert_from_path(pdf_path)
            
            page_files = []
            for i, image in enumerate(images):
                page_filename = f"page_{i+1:03d}.jpg"
                page_path = os.path.join(chapter_dir, page_filename)
                image.save(page_path, "JPEG")
                page_files.append(page_filename)
                
            if page_files:
                pages_data = ",".join(page_files)
                page_count = len(page_files)
                flash(f"PDF extracted successfully! {page_count} pages found.", "info")
            else:
                # Fallback if no images extracted
                 pages_data = pdf_filename
                 page_count = 1
                 
        except Exception as e:
            print(f"PDF Conversion Error: {e}")
            # Fallback to just storing PDF
            pages_data = pdf_filename
            page_count = 1
            flash(f"Warning: PDF saved but image conversion failed: {str(e)}", "warning")
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
    
    # Reward publisher 0.15$ per chapter
    try:
        # Get manga title for the reason
        c.execute("SELECT title FROM books WHERE id=?", (manga_id,))
        m_row = c.fetchone()
        manga_title = m_row[0] if m_row else "Unknown Manga"
        c.execute("""
            INSERT INTO publisher_earnings (user_id, request_id, amount, reason)
            VALUES (?, ?, ?, ?)
        """, (session['user_id'], None, 0.15, f"Chapter Upload Reward: {manga_title} Ch {chapter_num}"))
    except Exception as e:
        print(f"Error rewarding publisher for Ch {chapter_num}: {e}")
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
@admin_required
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


# API endpoint to get chapters for a manga
@app.route('/api/manga/<int:manga_id>/chapters', methods=['GET'])
@admin_required
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
        SELECT id, username, role, avatar_url, plan
        FROM users
        WHERE id = ?
    """, (user_id,))

    user = c.fetchone()
    if not user:
        conn.close()
        flash('User not found.', 'danger')
        return redirect(url_for('home'))

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

    # Get avatar settings
    profile_avatar_settings = fetch_user_avatar_settings(user_id)

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

    return render_template('user_profile.html',
                         user=user,
                         read_count=read_count,
                         watchlist_stats=watchlist_stats,
                         fav_count=fav_count,
                         recent_activity=recent_activity,
                         profile_avatar_settings=profile_avatar_settings)



# ---------- Manga Progress Tracking ----------
@app.route('/api/manga/progress', methods=['GET'])
def get_manga_progress():
    """Get the user's reading progress for a specific manga."""
    if 'user_id' not in session:
        return jsonify({'error': 'login required'}), 401
    
    manga_id = request.args.get('manga_id', type=int)
    if not manga_id:
        return jsonify({'error': 'manga_id required'}), 400
        
    conn = get_conn()
    c = conn.cursor()
    
    c.execute("""
        SELECT chapter_id, page_index
        FROM manga_progress
        WHERE user_id = ? AND manga_id = ?
    """, (session['user_id'], manga_id))
    
    row = c.fetchone()
    conn.close()
    
    if row:
        return jsonify({
            'success': True,
            'chapter_id': row[0],
            'page_index': row[1]
        })
    else:
        return jsonify({'success': True, 'chapter_id': None, 'page_index': 0})

@app.route('/api/manga/progress', methods=['POST'])
def save_manga_progress():
    """Save the user's reading progress."""
    if 'user_id' not in session:
        return jsonify({'error': 'login required'}), 401
    
    data = request.get_json(silent=True) or {}
    manga_id = data.get('manga_id')
    chapter_id = data.get('chapter_id')
    page_index = data.get('page_index', 0)
    
    if not manga_id or not chapter_id:
        return jsonify({'error': 'manga_id and chapter_id required'}), 400
        
    conn = get_conn()
    c = conn.cursor()
    
    try:
        c.execute("""
            INSERT INTO manga_progress (user_id, manga_id, chapter_id, page_index, updated_at)
            VALUES (?, ?, ?, ?, DATETIME('now'))
            ON CONFLICT(user_id, manga_id) DO UPDATE SET
                chapter_id = excluded.chapter_id,
                page_index = excluded.page_index,
                updated_at = excluded.updated_at
        """, (session['user_id'], manga_id, chapter_id, page_index))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500


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
    try:
        if "user_id" not in session:
            return redirect(url_for("login"))

        user_id = session["user_id"]
        role = session.get("role")

        q = request.args.get("q", "").strip()

        conn = get_conn()
        c = conn.cursor()

        base_query = """
            SELECT id, title, author,
                   COALESCE(category,'General') AS category,
                   pdf_filename,
                   audio_filename,
                   cover_path,
                   created_at,
                   COALESCE(book_type, 'book') AS book_type
            FROM books
            WHERE 1=1
        """
        params = []

        if role != "admin":
            base_query += " AND uploader_id = ?"
            params.append(user_id)

        if q:
            base_query += " AND (title LIKE ? OR author LIKE ?)"
            wildcard_q = f"%{q}%"
            params.extend([wildcard_q, wildcard_q])

        base_query += " ORDER BY datetime(created_at) DESC"

        c.execute(base_query, tuple(params))
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
                count_row = c.fetchone()
                count = count_row[0] if count_row else 0
                manga_chapters[book[0]] = count

        conn.close()

        return render_template("my_uploads.html", books=books, is_admin=(role == "admin"), manga_chapters=manga_chapters, q=q)
    except Exception as e:
        logger.error(f"Error in my_uploads: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        flash("An error occurred while loading your uploads.", "danger")
        return redirect(url_for("home"))


# ---------- Team Admin ----------
# ---------- TEAM ADMIN ----------

@app.route("/admin/users", methods=["GET", "POST"], endpoint="user_management")
@admin_required
def admin_users():
    conn = get_conn()
    c = conn.cursor()

    # Get total count
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]

    # Get first 20 users
    c.execute("SELECT id, username, role, COALESCE(is_banned,0) as is_banned, COALESCE(status,'active') as status, COALESCE(avatar_url, NULL) as avatar_url, COALESCE(plan,'basic') as plan, email, password FROM users ORDER BY username LIMIT 20")
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
    return render_template("user_management.html", users=users, pending=pending, total_users=total_users)


@app.route("/admin/users/load_more")
@admin_required
def load_more_users():
    offset = request.args.get("offset", 0, type=int)
    limit = 20
    
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, username, role, COALESCE(is_banned,0) as is_banned, COALESCE(status,'active') as status, COALESCE(avatar_url, NULL) as avatar_url, COALESCE(plan,'basic') as plan, email, password FROM users ORDER BY username LIMIT ? OFFSET ?", (limit, offset))
    users = c.fetchall()
    conn.close()
    
    return render_template("user_rows_partial.html", users=users)


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

# -------------------- CUSTOMIZATION / ANIMATIONS --------------------
@app.route("/customization")
def customization():
    """Customization page for managing animations - all users can view, only admin can upload"""
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    user_id = session.get("user_id")
    conn = get_conn()
    c = conn.cursor()
    
    # Get all custom animations for this user
    c.execute("""
        SELECT id, animation_type, file_path, is_active, created_at, COALESCE(has_animated, 0), name, category, user_id, min_plan
        FROM custom_animations
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user_id,))
    user_animations = c.fetchall()

    # Get GLOBAL animations (uploaded by admins)
    c.execute("""
        SELECT ca.id, ca.animation_type, ca.file_path, ca.is_active, ca.created_at, COALESCE(ca.has_animated, 0), ca.name, ca.category, ca.user_id, ca.min_plan
        FROM custom_animations ca
        JOIN users u ON ca.user_id = u.id
        WHERE u.role = 'admin'
        ORDER BY ca.created_at DESC
    """)
    global_animations = c.fetchall()

    # Determine User's Plan Level
    conn = get_conn() # Re-open just to be safe or reuse c if it's the same conn
    # users table has 'plan' column: basic, pro, ultimate
    c.execute("SELECT plan, role FROM users WHERE id = ?", (user_id,))
    user_row = c.fetchone()
    user_plan = user_row[0] if user_row else 'basic'
    user_role = user_row[1] if user_row else 'user'
    
    plan_levels = {'basic': 0, 'pro': 1, 'ultimate': 2, 'admin': 3}
    user_level = plan_levels.get(user_plan, 0)
    if user_role == 'admin':
        user_level = 3 # Admins see everything

    # Merge lists
    user_file_paths = {row[2] for row in user_animations}
    
    animations = list(user_animations)
    for anim in global_animations:
        # anim[9] is min_plan
        min_plan = anim[9] or 'basic'
        req_level = plan_levels.get(min_plan, 0)
        
        # Filter: Only show if user level >= required level
        if user_level >= req_level:
             # If user doesn't have this file path, add it as a global option
            if anim[2] not in user_file_paths:
                animations.append(anim)

    
    # Organize animations by type
    animations_dict = {
        'login': [],
        'manga_enter': [],
        'logout': [],
        'banner': []
    }
    
    active_animations = {}
    
    for anim in animations:
        anim_data = {
            'id': anim[0],
            'type': anim[1],
            'path': anim[2],
            'is_active': anim[3] if anim[8] == user_id else 0, # Only show active if it's THEIR copy
            'created_at': anim[4],
            'has_animated': anim[5],
            'name': anim[6],
            'category': anim[7],
            'is_global': (anim[8] != user_id), # Flag if it belongs to admin
            'min_plan': anim[9] or 'basic'
        }
        if anim[1] in animations_dict:
            animations_dict[anim[1]].append(anim_data)
        if anim[3] == 1:  # is_active
            active_animations[anim[1]] = anim_data
    
    # Get animation styles (from context processor logic but here for explicit template use if needed)
    # Actually inject_animations context processor handles results in 'anim_styles'
    
    # SYSTEM PRESETS
    # Login Preset
    has_login_default = any('hero-anime.jpg' in a['path'] for a in animations_dict['login'])
    if not has_login_default:
        animations_dict['login'].insert(0, {
            'id': 'preset_login_default',
            'type': 'login',
            'path': 'img/hero-anime.jpg',
            'is_active': 0,
            'name': 'Default Login Hero',
            'category': 'animation'
        })

    # Novus Blue Banner (Dashboard)
    has_novus_blue = any('banner_option_novus_blue.png' in a['path'] for a in animations_dict['banner'])
    if not has_novus_blue:
        animations_dict['banner'].insert(0, {
            'id': 'preset_novus_blue',
            'type': 'banner',
            'path': 'img/banner_option_novus_blue.png',
            'is_active': 0,
            'name': 'Novus Blue (Animated)',
            'category': 'animation'
        })

    # Jungle Presets (Only add if no user-uploaded 'jungle' version exists)
    # This prevents the user's "Moonlit Jungle" from appearing next to a duplicate system preset.
    
    # Jungle Login
    has_jungle_login = any('jungle' in a['path'].lower() or 'jungle' in a['name'].lower() for a in animations_dict['login'])
    if not has_jungle_login:
        animations_dict['login'].append({
            'id': 'preset_jungle_login',
            'type': 'login',
            'path': 'img/jungle_login.png',
            'is_active': 0,
            'name': 'Jungle Ruins',
            'category': 'animation'
        })

    # Jungle Manga Enter
    has_jungle_manga = any('jungle' in a['path'].lower() or 'jungle' in a['name'].lower() for a in animations_dict['manga_enter'])
    if not has_jungle_manga:
        animations_dict['manga_enter'].append({
            'id': 'preset_jungle_manga',
            'type': 'manga_enter',
            'path': 'img/jungle_manga.png',
            'is_active': 0,
            'name': 'Jungle Temple Path',
            'category': 'animation'
        })

    # Jungle Logout
    has_jungle_logout = any('jungle' in a['path'].lower() or 'jungle' in a['name'].lower() for a in animations_dict['logout'])
    if not has_jungle_logout:
        animations_dict['logout'].append({
            'id': 'preset_jungle_logout',
            'type': 'logout',
            'path': 'img/jungle_logout.png',
            'is_active': 0,
            'name': 'Moonlit Jungle',
            'category': 'animation'
        })

    # Manga Enter Preset
    has_manga_default = any('manga_enter_default.png' in a['path'] for a in animations_dict['manga_enter'])
    if not has_manga_default:
        animations_dict['manga_enter'].insert(0, {
            'id': 'preset_manga_default',
            'type': 'manga_enter',
            'path': 'img/manga_enter_default.png',
            'is_active': 0,
            'name': 'Default Manga Slide',
            'category': 'animation'
        })

    # Logout Preset
    has_logout_default = any('logout_default.png' in a['path'] for a in animations_dict['logout'])
    if not has_logout_default:
        animations_dict['logout'].insert(0, {
            'id': 'preset_logout_default',
            'type': 'logout',
            'path': 'img/logout_default.png',
            'is_active': 0,
            'name': 'Default Logout Ease',
            'category': 'animation'
        })

    conn.close()
    return render_template("customization.html", 
                         all_animations=animations_dict,
                         active_animations=active_animations,
                         user_plan=user_plan,
                         user_role=user_role)

@app.route("/customization/library")
@admin_required
def customization_library():
    """New Animation Library Page"""
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    user_id = session.get("user_id")
    conn = get_conn()
    c = conn.cursor()
    
    # Get User Plan
    c.execute("SELECT plan, role FROM users WHERE id = ?", (user_id,))
    user_row = c.fetchone()
    user_plan = user_row[0] if user_row else 'basic'
    user_role = user_row[1] if user_row else 'user'

    # Get ALL Global Animations (Admin) + User Animations
    # We want to display everything for the library view
    
    # 1. User's own
    c.execute("""
        SELECT id, animation_type, file_path, is_active, created_at, COALESCE(has_animated, 0), name, category, user_id, min_plan
        FROM custom_animations
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user_id,))
    user_anims = c.fetchall()

    # 2. Global (Admin)
    c.execute("""
        SELECT ca.id, ca.animation_type, ca.file_path, ca.is_active, ca.created_at, COALESCE(ca.has_animated, 0), ca.name, ca.category, ca.user_id, ca.min_plan
        FROM custom_animations ca
        JOIN users u ON ca.user_id = u.id
        WHERE u.role = 'admin'
        ORDER BY ca.created_at DESC
    """)
    global_anims = c.fetchall()

    conn.close()

    animations_dict = {
        'login': [], 'banner': [], 'manga_enter': [], 'logout': []
    }

    def to_dict(row, is_owned):
        return {
            'id': row[0],
            'type': row[1],
            'path': row[2],
            'is_active': row[3],
            'name': row[6],
            'category': row[7],
            'min_plan': row[9] or 'basic',
            'is_owned': is_owned
        }

    # Add Global
    for row in global_anims:
        d = to_dict(row, False)
        # Mark active? We need to know if it's active for THIS user.
        # But 'is_active' in global row refers to Admin's active state? No, is_active is per row.
        # Admin's row is_active=1 means Admin has it active. Irrelevant for user.
        # We need to check if user has THIS animation active. 
        # But user activates a COPY usually? Or references it?
        # Our system clones on activation. So the global animation itself is never "active" for the user directly?
        # Wait, previous logic was: Activate -> Clone.
        # So in the library, Global items are "Templates".
        if d['type'] in animations_dict:
            animations_dict[d['type']].append(d)

    # Add User's (which might be clones or originals)
    for row in user_anims:
        d = to_dict(row, True)
        if d['type'] in animations_dict:
            animations_dict[d['type']].append(d)

    return render_template("customization_library.html",
                         all_animations=animations_dict,
                         user_plan=user_plan,
                         user_role=user_role)

@app.route("/customization/upload")
@admin_required
def customization_upload():
    """Admin-only page for uploading custom animations"""
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    user_id = session.get("user_id")
    conn = get_conn()
    c = conn.cursor()
    
    # Get all animations for this user (admin)
    c.execute("""
        SELECT id, animation_type, file_path, is_active, created_at, COALESCE(has_animated, 0), name, category, min_plan
        FROM custom_animations
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user_id,))
    animations = c.fetchall()
    
    # Organize animations by type
    animations_dict = {
        'login': [],
        'manga_enter': [],
        'logout': [],
        'banner': []
    }
    
    active_animations = {}
    
    for anim in animations:
        anim_data = {
            'id': anim[0],
            'type': anim[1],
            'path': anim[2],
            'is_active': anim[3],
            'created_at': anim[4],
            'has_animated': anim[5],
            'name': anim[6],
            'category': anim[7],
            'min_plan': anim[8] or 'basic'
        }
        if anim[1] in animations_dict:
            animations_dict[anim[1]].append(anim_data)
        if anim[3] == 1:  # is_active
            active_animations[anim[1]] = anim_data
    
    
    # SYSTEM PRESETS (Added manually to ensure visibility)
    # Check if Novus Blue Circuit matches any existing user animation
    has_novus_blue_in_db = any('banner_option_novus_blue.png' in a['path'] for a in animations_dict['banner'])
    if not has_novus_blue_in_db:
        animations_dict['banner'].insert(0, {
            'id': 'preset_novus_blue',
            'type': 'banner',
            'path': 'img/banner_option_novus_blue.png',
            'is_active': 0,
            'created_at': 'System',
            'name': 'Novus Blue (Animated)',
            'category': 'style'
        })

    # Apply similar jungle pruning to upload page too
    for cat in ['login', 'manga_enter', 'logout']:
        has_jungle = any('jungle' in a['path'].lower() or 'jungle' in a['name'].lower() for a in animations_dict[cat])
        if not has_jungle:
            preset_name = 'Jungle Ruins' if cat == 'login' else ('Jungle Temple Path' if cat == 'manga_enter' else 'Moonlit Jungle')
            animations_dict[cat].append({
                'id': f'preset_jungle_{cat.split("_")[0]}',
                'type': cat,
                'path': f'img/jungle_{cat.split("_")[0]}.png',
                'is_active': 0,
                'name': preset_name,
                'category': 'animation'
            })

    conn.close()
    
    return render_template("customization_upload.html", 
                         all_animations=animations_dict,
                         active_animations=active_animations)



@app.route("/api/animation/upload", methods=["POST"])
def upload_animation():
    """Upload a custom animation"""
    # Ensure user is logged in and is admin for API endpoint
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    if session.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403
    
    animation_type = request.form.get("animation_type")
    if animation_type not in ["login", "manga_enter", "logout", "banner"]:
        return jsonify({"error": "Invalid animation type"}), 400
    
    animation_file = request.files.get("animation_file")
    if not animation_file or not animation_file.filename:
        return jsonify({"error": "No file uploaded"}), 400
    
    # Check file size (safely)
    file_size = getattr(animation_file, "content_length", None) or request.content_length
    if file_size and file_size > MAX_ANIMATION_SIZE:
        return jsonify({"error": f"File too large. Max size is {MAX_ANIMATION_SIZE // (1024*1024)}MB"}), 400
    
    # Check file extension
    ext = animation_file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_ANIMATION:
        return jsonify({"error": f"Invalid file type. Allowed: {', '.join(ALLOWED_ANIMATION)}"}), 400
    
    # Save file
    filename = secure_filename(animation_file.filename)
    timestamp = int(datetime.now().timestamp())
    unique_filename = f"{timestamp}_{filename}"
    
    subfolder = os.path.join(UPLOAD_FOLDER_ANIMATIONS, animation_type)
    os.makedirs(subfolder, exist_ok=True)
    file_path = os.path.join(subfolder, unique_filename)
    animation_file.save(file_path)
    
    relative_path = f"animations/{animation_type}/{unique_filename}"
    user_id = session.get("user_id")
    
    # Get has_animated parameter (defaults to 0 for backwards compatibility)
    has_animated = 1 if request.form.get("has_animated") == "true" else 0
    name = request.form.get("animation_name")
    min_plan = request.form.get("min_plan", "basic")
    
    category = request.form.get("category", "animation")
    
    accent_color = request.form.get("accent_color")
    
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO custom_animations (user_id, animation_type, file_path, is_active, has_animated, name, category, min_plan, accent_color)
        VALUES (?, ?, ?, 0, ?, ?, ?, ?, ?)
    """, (user_id, animation_type, relative_path, has_animated, name, category, min_plan, accent_color))
    animation_id = c.lastrowid
    conn.commit()
    conn.close()
    
    log_system_event('INFO', 'upload', f'Admin uploaded custom animation: {animation_type}', user_id, {'animation_id': animation_id, 'min_plan': min_plan})
    
    return jsonify({
        "success": True,
        "animation": {
            "id": animation_id,
            "type": animation_type,
            "path": relative_path,
            "name": name,
            "category": category,
            "min_plan": min_plan
        }
    })


@app.route("/api/animation/<int:anim_id>/update", methods=["POST"])
@admin_required
def update_animation_api(anim_id):
    """Update animation details (name/category/min_plan)"""
    data = request.json
    name = data.get('name')
    category = data.get('category')
    min_plan = data.get('min_plan', 'basic') 
    accent_color = data.get('accent_color')
    
    if not name or not category:
        return jsonify({"error": "Missing required fields"}), 400
        
    conn = get_conn()
    c = conn.cursor()
    
    # Verify ownership or admin
    c.execute("UPDATE custom_animations SET name = ?, category = ?, min_plan = ?, accent_color = ? WHERE id = ?", (name, category, min_plan, accent_color, anim_id))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True})


@app.route("/api/animation/<int:anim_id>/delete", methods=["DELETE"])
@admin_required
def delete_animation_api(anim_id):
    """Delete an animation and its associated file"""
    conn = get_conn()
    c = conn.cursor()
    
    # Get file path first
    c.execute("SELECT file_path FROM custom_animations WHERE id = ?", (anim_id,))
    row = c.fetchone()
    
    if not row:
        conn.close()
        return jsonify({"error": "Animation not found"}), 404
        
    file_path = row[0]
    
    # Delete from DB
    c.execute("DELETE FROM custom_animations WHERE id = ?", (anim_id,))
    conn.commit()
    conn.close()
    
    # Delete file from disk if it exists and is not a preset
    if file_path and not file_path.startswith('img/'):
        full_path = os.path.join(APP_ROOT, "static", file_path)
        if os.path.exists(full_path):
            try:
                os.remove(full_path)
            except Exception as e:
                print(f"Error deleting file: {e}")
                
    return jsonify({"success": True})


@app.route("/api/animation/<animation_id>/activate", methods=["PUT"])
def activate_animation(animation_id):
    """Set an animation style or custom upload as active"""
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    user_id = session.get("user_id")
    data = request.get_json() or {}
    category = data.get('category')
    
    conn = get_conn()
    c = conn.cursor()

    # Define valid style presets
    style_presets = [
        'standard', 'glitch', 'neon', 'blur', 'jungle', # login
        'classic', 'warp', 'slide_up', 'zoom', 'jungle', 'cave', # manga
        'none', 'cyber', 'matrix', 'grid',           # dashboard/banner
        'fade', 'shutter', 'pixel', 'shrink', 'bounce', 'jungle' # logout
    ]

    # Map categories to DB setting keys
    cat_to_setting = {
        'login': 'login',
        'manga_enter': 'manga',
        'banner': 'dashboard',
        'logout': 'logout'
    }

    # 1. Handle Style Presets
    if animation_id in style_presets:
        if not category:
            return jsonify({"error": "Category required for style presets"}), 400
        
        setting_key = cat_to_setting.get(category, category)
        
        # Deactivate custom animations for this category
        c.execute("UPDATE custom_animations SET is_active = 0 WHERE user_id = ? AND animation_type = ?", (user_id, category))
        
        # Save style setting
        c.execute("""
            INSERT INTO animation_settings (user_id, setting_key, setting_value)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, setting_key) DO UPDATE SET setting_value = excluded.setting_value
        """, (user_id, setting_key, animation_id))
        
        conn.commit()
        conn.close()
        return jsonify({"success": True, "mode": "style", "value": animation_id})

    # 2. Handle Resets
    if animation_id.startswith('reset_'):
        reset_type = animation_id.replace('reset_', '')
        setting_key = cat_to_setting.get(reset_type, reset_type)
        
        c.execute("UPDATE custom_animations SET is_active = 0 WHERE user_id = ? AND animation_type = ?", (user_id, reset_type))
        
        # Reset to default style
        defaults = {'login': 'standard', 'manga': 'classic', 'dashboard': 'none', 'logout': 'fade'}
        default_val = defaults.get(setting_key, 'default')
        
        c.execute("""
            INSERT INTO animation_settings (user_id, setting_key, setting_value)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, setting_key) DO UPDATE SET setting_value = excluded.setting_value
        """, (user_id, setting_key, default_val))
        
        conn.commit()
        conn.close()
        return jsonify({"success": True, "mode": "reset"})

    # 3. Handle System Presets (legacy/special)
    if animation_id == 'preset_jungle_login':
        c.execute("UPDATE custom_animations SET is_active = 0 WHERE user_id = ? AND animation_type = 'login'", (user_id,))
        preset_path = 'img/jungle_login.png'
        c.execute("INSERT INTO animation_settings (user_id, setting_key, setting_value) VALUES (?, 'login', 'standard') ON CONFLICT(user_id, setting_key) DO UPDATE SET setting_value = 'standard'", (user_id,))
        c.execute("SELECT id FROM custom_animations WHERE user_id = ? AND file_path LIKE ?", (user_id, f"%{preset_path}%"))
        row = c.fetchone()
        if row: c.execute("UPDATE custom_animations SET is_active = 1 WHERE id = ?", (row[0],))
        else: c.execute("INSERT INTO custom_animations (user_id, animation_type, file_path, is_active, name, category) VALUES (?, 'login', ?, 1, 'Jungle Ruins', 'animation')", (user_id, preset_path))
        conn.commit()
        conn.close()
        return jsonify({"success": True})

    if animation_id == 'preset_jungle_manga':
        c.execute("UPDATE custom_animations SET is_active = 0 WHERE user_id = ? AND animation_type = 'manga_enter'", (user_id,))
        preset_path = 'img/jungle_manga.png'
        c.execute("INSERT INTO animation_settings (user_id, setting_key, setting_value) VALUES (?, 'manga', 'jungle') ON CONFLICT(user_id, setting_key) DO UPDATE SET setting_value = 'jungle'", (user_id,))
        c.execute("SELECT id FROM custom_animations WHERE user_id = ? AND file_path LIKE ?", (user_id, f"%{preset_path}%"))
        row = c.fetchone()
        if row: c.execute("UPDATE custom_animations SET is_active = 1 WHERE id = ?", (row[0],))
        else: c.execute("INSERT INTO custom_animations (user_id, animation_type, file_path, is_active, name, category) VALUES (?, 'manga_enter', ?, 1, 'Jungle Temple Path', 'animation')", (user_id, preset_path))
        conn.commit()
        conn.close()
        return jsonify({"success": True})

    if animation_id == 'preset_jungle_logout':
        c.execute("UPDATE custom_animations SET is_active = 0 WHERE user_id = ? AND animation_type = 'logout'", (user_id,))
        preset_path = 'img/jungle_logout.png'
        c.execute("INSERT INTO animation_settings (user_id, setting_key, setting_value) VALUES (?, 'logout', 'fade') ON CONFLICT(user_id, setting_key) DO UPDATE SET setting_value = 'fade'", (user_id,))
        c.execute("SELECT id FROM custom_animations WHERE user_id = ? AND file_path LIKE ?", (user_id, f"%{preset_path}%"))
        row = c.fetchone()
        if row: c.execute("UPDATE custom_animations SET is_active = 1 WHERE id = ?", (row[0],))
        else: c.execute("INSERT INTO custom_animations (user_id, animation_type, file_path, is_active, name, category) VALUES (?, 'logout', ?, 1, 'Moonlit Jungle', 'animation')", (user_id, preset_path))
        conn.commit()
        conn.close()
        return jsonify({"success": True})

    if animation_id == 'preset_login_default':
        c.execute("UPDATE custom_animations SET is_active = 0 WHERE user_id = ? AND animation_type = 'login'", (user_id,))
        preset_path = 'img/hero-anime.jpg'
        c.execute("INSERT INTO animation_settings (user_id, setting_key, setting_value) VALUES (?, 'login', 'standard') ON CONFLICT(user_id, setting_key) DO UPDATE SET setting_value = 'standard'", (user_id,))
        
        c.execute("SELECT id FROM custom_animations WHERE user_id = ? AND file_path LIKE ?", (user_id, f"%{preset_path}%"))
        row = c.fetchone()
        if row:
            c.execute("UPDATE custom_animations SET is_active = 1 WHERE id = ?", (row[0],))
        else:
            c.execute("INSERT INTO custom_animations (user_id, animation_type, file_path, is_active, name, category) VALUES (?, 'login', ?, 1, 'Default Login Hero', 'animation')", (user_id, preset_path))
        conn.commit()
        conn.close()
        return jsonify({"success": True})

    if animation_id == 'preset_novus_blue':
        c.execute("UPDATE custom_animations SET is_active = 0 WHERE user_id = ? AND animation_type = 'banner'", (user_id,))
        preset_path = 'img/banner_option_novus_blue.png'
        # Set style to 'none' so it doesn't try to apply glitch effects over it
        c.execute("INSERT INTO animation_settings (user_id, setting_key, setting_value) VALUES (?, 'dashboard', 'none') ON CONFLICT(user_id, setting_key) DO UPDATE SET setting_value = 'none'", (user_id,))
        
        c.execute("SELECT id FROM custom_animations WHERE user_id = ? AND file_path LIKE ?", (user_id, f"%{preset_path}%"))
        row = c.fetchone()
        if row:
            c.execute("UPDATE custom_animations SET is_active = 1 WHERE id = ?", (row[0],))
        else:
            c.execute("INSERT INTO custom_animations (user_id, animation_type, file_path, is_active, name, category) VALUES (?, 'banner', ?, 1, 'Novus Blue', 'animation')", (user_id, preset_path))
        conn.commit()
        conn.close()
        return jsonify({"success": True})

    if animation_id == 'preset_manga_default':
        c.execute("UPDATE custom_animations SET is_active = 0 WHERE user_id = ? AND animation_type = 'manga_enter'", (user_id,))
        preset_path = 'img/manga_enter_default.png'
        c.execute("INSERT INTO animation_settings (user_id, setting_key, setting_value) VALUES (?, 'manga', 'classic') ON CONFLICT(user_id, setting_key) DO UPDATE SET setting_value = 'classic'", (user_id,))
        
        c.execute("SELECT id FROM custom_animations WHERE user_id = ? AND file_path LIKE ?", (user_id, f"%{preset_path}%"))
        row = c.fetchone()
        if row:
            c.execute("UPDATE custom_animations SET is_active = 1 WHERE id = ?", (row[0],))
        else:
            c.execute("INSERT INTO custom_animations (user_id, animation_type, file_path, is_active, name, category) VALUES (?, 'manga_enter', ?, 1, 'Default Manga Slide', 'animation')", (user_id, preset_path))
        conn.commit()
        conn.close()
        return jsonify({"success": True})

    if animation_id == 'preset_logout_default':
        c.execute("UPDATE custom_animations SET is_active = 0 WHERE user_id = ? AND animation_type = 'logout'", (user_id,))
        preset_path = 'img/logout_default.png'
        c.execute("INSERT INTO animation_settings (user_id, setting_key, setting_value) VALUES (?, 'logout', 'fade') ON CONFLICT(user_id, setting_key) DO UPDATE SET setting_value = 'fade'", (user_id,))
        
        c.execute("SELECT id FROM custom_animations WHERE user_id = ? AND file_path LIKE ?", (user_id, f"%{preset_path}%"))
        row = c.fetchone()
        if row:
            c.execute("UPDATE custom_animations SET is_active = 1 WHERE id = ?", (row[0],))
        else:
            c.execute("INSERT INTO custom_animations (user_id, animation_type, file_path, is_active, name, category) VALUES (?, 'logout', ?, 1, 'Default Logout Ease', 'animation')", (user_id, preset_path))
        conn.commit()
        conn.close()
        return jsonify({"success": True})

    # 4. Handle Custom Animation IDs (Integer)
    try:
        anim_id = int(animation_id)
        
        # Check if animation exists and get ownership info
        c.execute("""
            SELECT ca.animation_type, ca.user_id, ca.file_path, ca.name, ca.category, ca.has_animated, u.role 
            FROM custom_animations ca
            JOIN users u ON ca.user_id = u.id
            WHERE ca.id = ?
        """, (anim_id,))
        row = c.fetchone()
        
        if not row:
            conn.close()
            return jsonify({"error": "Animation not found"}), 404
        
        anim_type, owner_id, file_path, name, category, has_animated, owner_role = row
        
        # LOGIC:
        # 1. If User owns it -> Just activate it
        # 2. If Admin owns it -> Clone it to User's library, then activate the clone
        
        target_anim_id = anim_id
        
        if owner_id != user_id:
            if owner_role == 'admin':
                # CLONE IT
                # Check if we already have a copy (sanity check)
                c.execute("SELECT id FROM custom_animations WHERE user_id = ? AND file_path = ?", (user_id, file_path))
                existing_copy = c.fetchone()
                
                if existing_copy:
                    target_anim_id = existing_copy[0]
                else:
                    c.execute("""
                        INSERT INTO custom_animations (user_id, animation_type, file_path, is_active, has_animated, name, category)
                        VALUES (?, ?, ?, 0, ?, ?, ?)
                    """, (user_id, anim_type, file_path, has_animated, name, category))
                    target_anim_id = c.lastrowid
            else:
                conn.close()
                return jsonify({"error": "Unauthorized to use this animation"}), 403

        # Now activate target_anim_id (which is definitely owned by user now)
        
        # Deactivate others of same type
        c.execute("UPDATE custom_animations SET is_active = 0 WHERE user_id = ? AND animation_type = ?", (user_id, anim_type))
        # Activate the target
        c.execute("UPDATE custom_animations SET is_active = 1 WHERE id = ?", (target_anim_id,))
        
        # AUTO-DETECT STYLE: If custom name/path contains 'jungle' or 'cave', set style to 'jungle'
        name_path = (str(name or "") + str(file_path or "")).lower()
        
        style_to_use = 'none'
        if 'jungle' in name_path or 'cave' in name_path:
            style_to_use = 'jungle'
        
        setting_key = cat_to_setting.get(anim_type, anim_type)
        c.execute("INSERT INTO animation_settings (user_id, setting_key, setting_value) VALUES (?, ?, ?) ON CONFLICT(user_id, setting_key) DO UPDATE SET setting_value = excluded.setting_value", (user_id, setting_key, style_to_use))
        
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except ValueError:
        return jsonify({"error": "Invalid Animation ID"}), 400


@app.route("/api/animation/<int:animation_id>", methods=["DELETE"])
@admin_required
def delete_animation(animation_id):
    """Delete an animation"""
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    user_id = session.get("user_id")
    conn = get_conn()
    c = conn.cursor()
    
    # Get animation file path
    c.execute("SELECT file_path FROM custom_animations WHERE id = ? AND user_id = ?",
              (animation_id, user_id))
    result = c.fetchone()
    
    if not result:
        conn.close()
        return jsonify({"error": "Animation not found"}), 404
    
    file_path = result[0]
    
    # Delete from database
    c.execute("DELETE FROM custom_animations WHERE id = ?", (animation_id,))
    conn.commit()
    conn.close()
    
    # Delete file from filesystem
    try:
        full_path = os.path.join(APP_ROOT, "static", file_path)
        if os.path.exists(full_path):
            os.remove(full_path)
    except Exception as e:
        print(f"Error deleting file: {e}")
    
    return jsonify({"success": True})



# -------------------- AVATAR STUDIO --------------------
@app.route("/avatar-studio")
def avatar_studio():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("avatar_studio.html")

@app.route("/api/avatar/save", methods=["POST"])
def save_avatar_settings():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    user_id = session["user_id"]
    data = request.json
    
    # settings keys: 'avatar_frame', 'avatar_border', 'avatar_color', 'avatar_bg', 'avatar_bg_class', 'avatar_bg_url', 'avatar_bg_filter', 'avatar_bg_brightness', 'avatar_bg_opacity', 'avatar_bg_blur', 'avatar_bg_match_color'
    allowed_keys = ['avatar_frame', 'avatar_border', 'avatar_color', 'avatar_bg', 'avatar_bg_class', 'avatar_bg_url', 'avatar_bg_filter', 'avatar_bg_brightness', 'avatar_bg_opacity', 'avatar_bg_blur', 'avatar_bg_match_color']
    
    conn = get_conn()
    c = conn.cursor()
    
    for key in allowed_keys:
        if key in data:
            val = data[key]
            c.execute("""
                INSERT INTO animation_settings (user_id, setting_key, setting_value)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, setting_key) DO UPDATE SET setting_value = excluded.setting_value
            """, (user_id, key, val))
            
    conn.commit()
    conn.close()
    
    return jsonify({"success": True})

@app.route("/api/avatar/upload-bg", methods=["POST"])
def upload_avatar_bg():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    if file and allowed(file.filename, ALLOWED_EXTS):
        filename = secure_filename(file.filename)
        # Create user specific bg folder to keep it clean
        user_bg_folder = os.path.join(APP_ROOT, "static", "uploads", "bg", str(session["user_id"]))
        os.makedirs(user_bg_folder, exist_ok=True)
        
        # Save file with timestamp to avoid caching/collisions
        import time
        unique_filename = f"{int(time.time())}_{filename}"
        file.save(os.path.join(user_bg_folder, unique_filename))
        
        # Return path relative to static
        path = f"/static/uploads/bg/{session['user_id']}/{unique_filename}"
        return jsonify({"success": True, "path": path})
        
    return jsonify({"error": "Invalid file type"}), 400

@app.route("/api/admin/upload-avatar-bg", methods=["POST"])
def upload_admin_avatar_bg():
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 401
    
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
        
    file = request.files['file']
    name = request.form.get('name')
    access_tag = request.form.get('access_tag')
    
    if not name or not access_tag:
        return jsonify({"error": "Missing metadata"}), 400

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    # Allow images and videos
    ALLOWED_BG_EXTS = {"png", "jpg", "jpeg", "webp", "gif", "mp4", "webm", "jfif"}
    if file and allowed(file.filename, ALLOWED_BG_EXTS):
        filename = secure_filename(file.filename)
        # Check video duration if video (skipped for now to avoid bulky deps, assuming admin compliance)
        
        # Save to shared backgrounds folder
        bg_folder = os.path.join(APP_ROOT, "static", "uploads", "bg", "library")
        os.makedirs(bg_folder, exist_ok=True)
        
        import time
        unique_filename = f"{int(time.time())}_{filename}"
        file.save(os.path.join(bg_folder, unique_filename))
        path = f"/static/uploads/bg/library/{unique_filename}"
        
        # Save to DB
        conn = get_conn()
        c = conn.cursor()
        c.execute("""
            INSERT INTO custom_animations (user_id, animation_type, file_path, name, access_tag, category)
            VALUES (?, 'avatar_bg', ?, ?, ?, 'avatar_bg')
        """, (session['user_id'], path, name, access_tag))
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "path": path})

    return jsonify({"error": "Invalid file type"}), 400

@app.route("/api/avatar/backgrounds", methods=["GET"])
def get_avatar_backgrounds():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401
        
    user_plan = session.get("plan", "basic").lower() # basic, pro, ultimate
    user_role = session.get("role", "user")
    
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, name, file_path, access_tag FROM custom_animations WHERE category='avatar_bg'")
    rows = c.fetchall()
    conn.close()
    
    # Filter based on plan
    # Logic: basic sees basic. pro sees basic+pro. ultimate sees basic+pro+ultimate. admin sees all.
    allowed = []
    
    plan_levels = {'basic': 1, 'pro': 2, 'ultimate': 3}
    user_level = plan_levels.get(user_plan, 1)
    
    for r in rows:
        bg_id, bg_name, bg_path, bg_tag = r
        bg_tag = bg_tag.lower()
        
        is_allowed = False
        
        if user_role == 'admin':
            is_allowed = True
        elif bg_tag == 'admin_only':
            is_allowed = False
        else:
            bg_level = plan_levels.get(bg_tag, 99) # Default to high if unknown
            if user_level >= bg_level:
                is_allowed = True
                
        if is_allowed:
            allowed.append({
                "id": bg_id,
                "name": bg_name,
                "path": bg_path,
                "tag": bg_tag
            })
            
    return jsonify({"backgrounds": allowed})

@app.route("/api/admin/background/<int:bg_id>", methods=["DELETE"])
def delete_admin_bg(bg_id):
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 403
        
    conn = get_conn()
    c = conn.cursor()
    
    # Get file path
    c.execute("SELECT file_path FROM custom_animations WHERE id = ? AND category='avatar_bg'", (bg_id,))
    row = c.fetchone()
    
    if row:
        path = row[0]
        # Remove from DB
        c.execute("DELETE FROM custom_animations WHERE id = ?", (bg_id,))
        conn.commit()
        
        # Remove file
        full_path = os.path.join(APP_ROOT, path.lstrip('/'))
        if os.path.exists(full_path):
            try:
                os.remove(full_path)
            except:
                pass
                
        conn.close()
        return jsonify({"success": True})
    
    conn.close()
    return jsonify({"error": "Not found"}), 404

@app.route("/api/admin/background/<int:bg_id>", methods=["PUT"])
def edit_admin_bg(bg_id):
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 403
        
    data = request.json
    name = data.get('name')
    access_tag = data.get('access_tag')
    
    if not name or not access_tag:
        return jsonify({"error": "Missing data"}), 400
        
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE custom_animations SET name = ?, access_tag = ? WHERE id = ? AND category='avatar_bg'", (name, access_tag, bg_id))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True})


    return jsonify({"backgrounds": allowed})

def fetch_user_avatar_settings(user_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT setting_key, setting_value FROM animation_settings WHERE user_id = ?", (user_id,))
    rows = c.fetchall()
    conn.close()
    
    settings = {}
    for key, val in rows:
        if key.startswith('avatar_'):
            settings[key] = val
    return settings

@app.context_processor
def inject_avatar_settings():
    if "user_id" not in session:
        return {}
    
    return {'avatar_settings': fetch_user_avatar_settings(session["user_id"])}


# -------------------- FAQ ROUTE --------------------
@app.route("/faq")
def faq():
    """Display FAQ & Guidelines page"""
    return render_template("faq.html")


# -------------------- TOOLS ROUTE --------------------
@app.route("/tools")
def tools():
    """Display Tools / Web Hub page"""
    if "user_id" not in session:
        return redirect(url_for("login"))
    is_admin = session.get("role") == "admin"
    return render_template("tools.html", is_admin=is_admin)


@app.route("/code-projects")
def code_projects():
    """Display dedicated Code Projects gallery page"""
    if "user_id" not in session:
        return redirect(url_for("login"))
    is_admin = session.get("role") == "admin"
    return render_template("code_projects.html", is_admin=is_admin)


# -------------------- TOOLS API ROUTES (Code Projects & Terminal) --------------------
import zipfile
import shutil
import subprocess
import json as json_module

CODE_PROJECTS_FOLDER = os.path.join("static", "code_projects")
os.makedirs(CODE_PROJECTS_FOLDER, exist_ok=True)

import re
def fix_html_paths(project_path):
    """Automatically convert absolute paths (/index.css) to relative in HTML files"""
    for dirpath, _, filenames in os.walk(project_path):
        for f in filenames:
            if f.endswith(".html"):
                fp = os.path.join(dirpath, f)
                try:
                    with open(fp, 'r', encoding='utf-8') as file:
                        content = file.read()
                    
                    # Replace href="/..." and src="/..." with relative versions
                    # We look for / but only if it's the start of the path
                    new_content = re.sub(r'(href|src)=["\']/(?!/)', r'\1="', content)
                    
                    if new_content != content:
                        with open(fp, 'w', encoding='utf-8') as file:
                            file.write(new_content)
                except Exception as e:
                    logger.error(f"Failed to fix paths in {fp}: {e}")


@app.route("/api/tools/upload-zip", methods=["POST"])
@admin_required
def tools_upload_zip():
    """Upload and extract a ZIP file as a code project"""
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files["file"]
    if not file.filename or not file.filename.lower().endswith(".zip"):
        return jsonify({"error": "File must be a ZIP archive"}), 400
    
    # Generate project name from filename
    project_name = secure_filename(file.filename.rsplit(".", 1)[0])
    if not project_name:
        project_name = f"project_{int(datetime.now().timestamp())}"
    
    # Create unique folder name if already exists
    base_name = project_name
    counter = 1
    while os.path.exists(os.path.join(CODE_PROJECTS_FOLDER, project_name)):
        project_name = f"{base_name}_{counter}"
        counter += 1
    
    project_path = os.path.join(CODE_PROJECTS_FOLDER, project_name)
    os.makedirs(project_path, exist_ok=True)
    
    # Save and extract ZIP
    zip_path = os.path.join(project_path, "temp.zip")
    try:
        file.save(zip_path)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(project_path)
        os.remove(zip_path)
        
        # Get project size
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(project_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
        
        # Fix paths
        fix_html_paths(project_path)
        
        return jsonify({
            "success": True,
            "project": {
                "name": project_name,
                "path": project_path,
                "size": total_size,
                "created_at": datetime.now().isoformat()
            }
        })
    except Exception as e:
        # Cleanup on error
        if os.path.exists(project_path):
            shutil.rmtree(project_path)
        return jsonify({"error": str(e)}), 500


@app.route("/api/tools/upload-files", methods=["POST"])
@admin_required
def tools_upload_files():
    """Upload multiple files to create a code project"""
    if "files" not in request.files:
        return jsonify({"error": "No files provided"}), 400
    
    project_name = request.form.get("project_name", "").strip()
    if not project_name:
        project_name = f"project_{int(datetime.now().timestamp())}"
    project_name = secure_filename(project_name)
    
    # Create unique folder
    base_name = project_name
    counter = 1
    while os.path.exists(os.path.join(CODE_PROJECTS_FOLDER, project_name)):
        project_name = f"{base_name}_{counter}"
        counter += 1
    
    project_path = os.path.join(CODE_PROJECTS_FOLDER, project_name)
    os.makedirs(project_path, exist_ok=True)
    
    try:
        files = request.files.getlist("files")
        for file in files:
            if file.filename:
                # Preserve folder structure from webkitRelativePath if available
                relative_path = request.form.get(f"path_{file.filename}", file.filename)
                file_path = os.path.join(project_path, secure_filename(relative_path.replace("/", os.sep)))
                os.makedirs(os.path.dirname(file_path), exist_ok=True) if os.path.dirname(file_path) else None
                file.save(file_path)
        
        # Get project size
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(project_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
        
        # Fix paths
        fix_html_paths(project_path)
        
        return jsonify({
            "success": True,
            "project": {
                "name": project_name,
                "path": project_path,
                "size": total_size,
                "created_at": datetime.now().isoformat()
            }
        })
    except Exception as e:
        if os.path.exists(project_path):
            shutil.rmtree(project_path)
        return jsonify({"error": str(e)}), 500


@app.route("/api/tools/projects", methods=["GET"])
def tools_list_projects():
    """List all uploaded code projects"""
    projects = []
    
    if os.path.exists(CODE_PROJECTS_FOLDER):
        for name in os.listdir(CODE_PROJECTS_FOLDER):
            project_path = os.path.join(CODE_PROJECTS_FOLDER, name)
            if os.path.isdir(project_path):
                # Calculate size
                total_size = 0
                file_count = 0
                for dirpath, dirnames, filenames in os.walk(project_path):
                    for f in filenames:
                        fp = os.path.join(dirpath, f)
                        total_size += os.path.getsize(fp)
                        file_count += 1
                
                # Get creation time
                created_at = datetime.fromtimestamp(os.path.getctime(project_path)).isoformat()
                
                projects.append({
                    "name": name,
                    "size": total_size,
                    "file_count": file_count,
                    "created_at": created_at
                })
    
    return jsonify({"projects": sorted(projects, key=lambda x: x["created_at"], reverse=True)})


@app.route("/api/tools/projects/<project_name>", methods=["DELETE"])
@admin_required
def tools_delete_project(project_name):
    """Delete a code project (Admin Only)"""
    project_name = secure_filename(project_name)
    project_path = os.path.join(CODE_PROJECTS_FOLDER, project_name)
    
    if not os.path.exists(project_path):
        return jsonify({"error": "Project not found"}), 404
    
    try:
        # Also delete any tool_links that reference this project
        conn = get_conn()
        c = conn.cursor()
        c.execute("DELETE FROM tool_links WHERE project_name = ?", (project_name,))
        conn.commit()
        conn.close()
        
        # Delete the project folder
        shutil.rmtree(project_path)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


from flask import send_from_directory
@app.route("/raw-project/<path:filepath>")
def serve_project_raw(filepath):
    """Serve project files with explicit MIME types and auto-extension resolution"""
    # filepath matches project_name/internal_path
    directory = CODE_PROJECTS_FOLDER # d:\nist project\computer\library\novus-library\static\code_projects
    full_path = os.path.join(directory, filepath)
    
    # Try adding extensions if file doesn't exist
    if not os.path.exists(full_path) and '.' not in os.path.basename(filepath):
        for ext in ['.tsx', '.ts', '.jsx', '.js']:
            if os.path.exists(full_path + ext):
                filepath += ext
                full_path += ext
                break

    mimetype = None
    file_ext = os.path.splitext(filepath)[1].lower()
    if file_ext in {'.ts', '.tsx', '.jsx'}:
        mimetype = 'application/javascript'
    elif file_ext == '.css':
        mimetype = 'text/css'
    
    return send_from_directory(directory, filepath, mimetype=mimetype)



# ---------- Tool Links Persistence API ----------

@app.route("/api/tools/links", methods=["GET"])
def tools_get_links():
    """Retrieve all tool links from the database"""
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    user_id = session["user_id"]
    conn = get_conn()
    c = conn.cursor()
    
    # Get user's plan
    user_plan = c.execute("SELECT plan FROM users WHERE id = ?", (user_id,)).fetchone()
    user_plan = user_plan[0] if user_plan else "basic"
    
    links = c.execute("""
        SELECT id, name, url, description, category, plan_required, icon_type, icon_value, is_project, project_name 
        FROM tool_links 
        ORDER BY created_at DESC
    """).fetchall()
    conn.close()
    
    plan_levels = {"basic": 0, "pro": 1, "ultimate": 2}
    user_level = plan_levels.get(user_plan, 0)
    
    return jsonify({
        "links": [{
            "id": row[0],
            "name": row[1],
            "url": row[2],
            "description": row[3],
            "category": row[4],
            "plan": row[5],
            "icon_type": row[6],
            "icon_value": row[7],
            "is_project": bool(row[8]),
            "project_name": row[9],
            "locked": plan_levels.get(row[5], 0) > user_level
        } for row in links]
    })


@app.route("/api/tools/projects/promote", methods=["POST"])
@admin_required
def tools_promote_project():
    """Promote a code project to a tool link"""
    # This might be multipart/form-data for an icon upload
    name = request.form.get("name")
    project_name = request.form.get("project_name")
    description = request.form.get("description", "")
    category = request.form.get("category", "tools")
    plan = request.form.get("plan", "basic")
    
    if not name or not project_name:
        return jsonify({"error": "Name and Project Name are required"}), 400
    
    icon_type = "fa"
    icon_value = "fas fa-code" # Default
    
    # Handle icon upload
    if "icon" in request.files:
        file = request.files["icon"]
        if file and file.filename:
            filename = secure_filename(f"icon_{project_name}_{file.filename}")
            icon_path = os.path.join("static", "uploads", "tool_icons", filename)
            file.save(os.path.join(APP_ROOT, icon_path))
            icon_type = "img"
            icon_value = "/" + icon_path.replace("\\", "/") # Ensure absolute path for web

    conn = get_conn()
    c = conn.cursor()
    # URL will be /project-view/<project_name>
    url = f"/project-view/{project_name}"
    
    c.execute("""
        INSERT INTO tool_links (name, url, description, category, plan_required, icon_type, icon_value, is_project, project_name)
        VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
    """, (name, url, description, category, plan, icon_type, icon_value, project_name))
    
    conn.commit()
    conn.close()
    
    return jsonify({"success": True})


@app.route("/project-view/<project_name>")
@login_required
def project_view(project_name):
    """Premium viewing page for code projects"""
    # Verify project exists
    project_path = os.path.join(CODE_PROJECTS_FOLDER, project_name)
    if not os.path.exists(project_path):
        flash("Project not found.", "danger")
        return redirect(url_for("tools"))
    
    return render_template("project_view.html", project_name=project_name)


@app.route("/api/tools/links", methods=["POST"])
@admin_required
def tools_add_link():
    """Add a new tool link (Admin Only)"""
    data = request.json
    if not data or not data.get("name") or not data.get("url"):
        return jsonify({"error": "Missing required fields"}), 400
    
    name = data.get("name")
    url = data.get("url")
    description = data.get("description", "")
    category = data.get("category", "work")
    plan = data.get("plan", "basic")
    icon_type = data.get("icon_type", "fa")
    icon_value = data.get("icon_value", "fas fa-globe")
    
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO tool_links (name, url, description, category, plan_required, icon_type, icon_value)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (name, url, description, category, plan, icon_type, icon_value))
    new_id = c.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "id": new_id})


@app.route("/api/tools/links/<int:link_id>", methods=["PUT"])
@admin_required
def tools_update_link(link_id):
    """Update an existing tool link (Admin Only)"""
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    conn = get_conn()
    c = conn.cursor()
    
    # Check if exists
    c.execute("SELECT id FROM tool_links WHERE id = ?", (link_id,))
    if not c.fetchone():
        conn.close()
        return jsonify({"error": "Link not found"}), 404
    
    # Update fields
    fields = []
    values = []
    
    mapping = {
        "name": "name",
        "url": "url",
        "description": "description",
        "category": "category",
        "plan": "plan_required",
        "icon_type": "icon_type",
        "icon_value": "icon_value"
    }
    
    for key, col in mapping.items():
        if key in data:
            fields.append(f"{col} = ?")
            values.append(data[key])
    
    if not fields:
        conn.close()
        return jsonify({"error": "Nothing to update"}), 400
    
    values.append(link_id)
    c.execute(f"UPDATE tool_links SET {', '.join(fields)} WHERE id = ?", values)
    conn.commit()
    conn.close()
    
    return jsonify({"success": True})


@app.route("/api/tools/links/<int:link_id>/update", methods=["POST"])
@admin_required
def tools_update_link_with_icon(link_id):
    """Update an existing tool link with icon file upload (Admin Only)"""
    conn = get_conn()
    c = conn.cursor()
    
    # Check if exists
    c.execute("SELECT id FROM tool_links WHERE id = ?", (link_id,))
    if not c.fetchone():
        conn.close()
        return jsonify({"error": "Link not found"}), 404
    
    # Get form data
    name = request.form.get("name")
    url = request.form.get("url")
    description = request.form.get("description", "")
    category = request.form.get("category", "work")
    plan = request.form.get("plan", "basic")
    
    icon_type = None
    icon_value = None
    
    # Handle icon upload
    if "icon" in request.files:
        file = request.files["icon"]
        if file and file.filename:
            filename = secure_filename(f"icon_{link_id}_{file.filename}")
            icon_path = os.path.join("static", "uploads", "tool_icons", filename)
            file.save(os.path.join(APP_ROOT, icon_path))
            icon_type = "img"
            icon_value = "/" + icon_path.replace("\\", "/")
    
    # Build update query
    update_fields = [
        "name = ?", "url = ?", "description = ?", 
        "category = ?", "plan_required = ?"
    ]
    values = [name, url, description, category, plan]
    
    if icon_type and icon_value:
        update_fields.extend(["icon_type = ?", "icon_value = ?"])
        values.extend([icon_type, icon_value])
    
    values.append(link_id)
    c.execute(f"UPDATE tool_links SET {', '.join(update_fields)} WHERE id = ?", values)
    conn.commit()
    conn.close()
    
    return jsonify({"success": True})


@app.route("/api/tools/links/<int:link_id>", methods=["DELETE"])
@admin_required
def tools_delete_link(link_id):
    """Delete a tool link (Admin Only)"""
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM tool_links WHERE id = ?", (link_id,))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True})


@app.route("/api/tools/projects/<project_name>/download", methods=["GET"])
@admin_required
def tools_download_project(project_name):
    """Download a project as ZIP"""
    project_name = secure_filename(project_name)
    project_path = os.path.join(CODE_PROJECTS_FOLDER, project_name)
    
    if not os.path.exists(project_path):
        return jsonify({"error": "Project not found"}), 404
    
    try:
        # Create ZIP in memory
        import io
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(project_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, project_path)
                    zf.write(file_path, arcname)
        
        memory_file.seek(0)
        response = make_response(memory_file.read())
        response.headers["Content-Type"] = "application/zip"
        response.headers["Content-Disposition"] = f"attachment; filename={project_name}.zip"
        return response
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/tools/terminal", methods=["POST"])
@admin_required
def tools_terminal():
    """Execute a terminal command in a project directory (ADMIN ONLY)"""
    data = request.get_json(silent=True) or {}
    command = data.get("command", "").strip()
    project_name = data.get("project", "").strip()
    
    if not command:
        return jsonify({"error": "No command provided"}), 400
        
    # Get current session CWD or default to CODE_PROJECTS_FOLDER
    session_cwd = session.get("terminal_cwd", CODE_PROJECTS_FOLDER)
    
    # If a specific project is selected in the UI dropdown, override session_cwd if not already inside it
    if project_name:
        project_name = secure_filename(project_name)
        project_root = os.path.join(CODE_PROJECTS_FOLDER, project_name)
        if not os.path.exists(project_root):
             return jsonify({"error": f"Project '{project_name}' not found"}), 404
        # If we aren't currently in this project or a subfolder of it, jump to its root
        if not session_cwd.startswith(project_root):
            session_cwd = project_root
            session["terminal_cwd"] = session_cwd

    cwd = session_cwd
    if not os.path.exists(cwd):
        cwd = CODE_PROJECTS_FOLDER
        session["terminal_cwd"] = cwd

    # Security: Block dangerous commands
    dangerous_patterns = [
        "rm -rf /", "rmdir /s", "format", "del /f /s /q",
        ":(){ :|:& };:", "mkfs", "dd if=", "> /dev/sda",
        "shutdown", "reboot", "halt", "poweroff", "rm ", "del "
    ]
    cmd_lower = command.lower()
    for pattern in dangerous_patterns:
        if pattern in cmd_lower:
            return jsonify({"error": "Command blocked for security reasons"}), 403

    # Handle 'cd' command specially
    if cmd_lower.startswith("cd "):
        target = command[3:].strip().strip('"').strip("'")
        if not target or target == "~":
            new_cwd = CODE_PROJECTS_FOLDER
        elif target == "..":
            new_cwd = os.path.dirname(cwd)
            # Don't allow going above CODE_PROJECTS_FOLDER
            if not os.path.abspath(new_cwd).startswith(os.path.abspath(CODE_PROJECTS_FOLDER)):
                new_cwd = CODE_PROJECTS_FOLDER
        else:
            new_cwd = os.path.abspath(os.path.join(cwd, target))
            if not new_cwd.startswith(os.path.abspath(CODE_PROJECTS_FOLDER)):
                return jsonify({"error": "Access denied"}), 403
            if not os.path.exists(new_cwd) or not os.path.isdir(new_cwd):
                return jsonify({"error": "Directory not found"}), 404
        
        session["terminal_cwd"] = new_cwd
        # Return success with updated path
        rel_path = os.path.relpath(new_cwd, CODE_PROJECTS_FOLDER)
        prompt_path = "~" if rel_path == "." else f"~/{rel_path.replace(os.sep, '/')}"
        return jsonify({
            "success": True, 
            "stdout": "", 
            "stderr": "", 
            "returncode": 0, 
            "cwd": prompt_path
        })

    try:
        # Run command with timeout
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )
        
        rel_path = os.path.relpath(cwd, CODE_PROJECTS_FOLDER)
        prompt_path = "~" if rel_path == "." else f"~/{rel_path.replace(os.sep, '/')}"

        return jsonify({
            "success": True,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "cwd": prompt_path
        })
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Command timed out (max 120 seconds)"}), 408
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/tools/terminal/files", methods=["GET"])
@admin_required
def tools_terminal_files():
    """List files in a project directory for the terminal"""
    project_name = request.args.get("project", "").strip()
    subpath = request.args.get("path", "").strip()
    
    if project_name:
        project_name = secure_filename(project_name)
        base_path = os.path.join(CODE_PROJECTS_FOLDER, project_name)
    else:
        base_path = CODE_PROJECTS_FOLDER
    
    if subpath:
        target_path = os.path.join(base_path, subpath)
    else:
        target_path = base_path
    
    if not os.path.exists(target_path):
        return jsonify({"error": "Path not found"}), 404
    
    items = []
    for name in os.listdir(target_path):
        item_path = os.path.join(target_path, name)
        items.append({
            "name": name,
            "is_dir": os.path.isdir(item_path),
            "size": os.path.getsize(item_path) if os.path.isfile(item_path) else 0
        })
    
    return jsonify({"items": sorted(items, key=lambda x: (not x["is_dir"], x["name"]))})


# -------------------- ERROR HANDLERS --------------------
@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file upload size limit exceeded"""
    flash("File upload failed: The uploaded file is too large. Please check file size limits.", "danger")
    return redirect(request.url)

# -------------------- BUNDLES ROUTES --------------------
@app.route("/bundles")
def bundles():
    """Main bundles page - login required"""
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    conn = get_conn()
    c = conn.cursor()
    
    c.execute("""
        SELECT id, slug, name, description, includes_json, theme_json, banner_preset, is_active, min_plan, icon_path
        FROM bundles
        WHERE is_active = 1
        ORDER BY id
    """)
    bundles_raw = c.fetchall()
    
    import json
    bundles_list = []
    for b in bundles_raw:
        bundles_list.append({
            "id": b[0],
            "slug": b[1],
            "name": b[2],
            "description": b[3],
            "includes": json.loads(b[4]) if b[4] else [],
            "theme": json.loads(b[5]) if b[5] else {},
            "banner_preset": b[6],
            "is_active": b[7],
            "min_plan": b[8],
            "icon_path": b[9]
        })
    
    # Get user plan
    user_plan = "basic"
    if "user_id" in session:
        c.execute("SELECT plan FROM users WHERE id = ?", (session["user_id"],))
        up = c.fetchone()
        if up:
            user_plan = up[0] or "basic"

    conn.close()
    return render_template("bundles.html", bundles=bundles_list, user_plan=user_plan)


@app.route("/admin/bundles")
@admin_required
def admin_bundles():
    """Admin bundles management page"""
    conn = get_conn()
    c = conn.cursor()
    
    c.execute("""
        SELECT id, slug, name, description, includes_json, theme_json, banner_preset, is_active, created_at, min_plan
        FROM bundles
        ORDER BY id
    """)
    bundles_raw = c.fetchall()
    conn.close()
    
    import json
    bundles_list = []
    for b in bundles_raw:
        bundles_list.append({
            "id": b[0],
            "slug": b[1],
            "name": b[2],
            "description": b[3],
            "includes": json.loads(b[4]) if b[4] else [],
            "theme": json.loads(b[5]) if b[5] else {},
            "banner_preset": b[6],
            "is_active": b[7],
            "created_at": b[8],
            "min_plan": b[9]
        })
    
    return render_template("admin_bundles.html", bundles=bundles_list)


@app.route("/admin/bundles/<int:id>/edit", methods=["GET", "POST"])
@admin_required
def admin_bundle_edit(id):
    """Admin bundle edit page"""
    import json
    conn = get_conn()
    c = conn.cursor()
    
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        slug = request.form.get("slug", "").strip()
        description = request.form.get("description", "").strip()
        includes_text = request.form.get("includes", "").strip()
        theme_json_text = request.form.get("theme_json", "{}").strip()
        banner_preset = request.form.get("banner_preset", "").strip()
        is_active = 1 if request.form.get("is_active") else 0
        min_plan = request.form.get("min_plan", "basic")
        
        # Handle icon upload
        icon_path = None
        icon_file = request.files.get("icon")
        if icon_file and icon_file.filename:
            from werkzeug.utils import secure_filename
            import os
            
            BUNDLE_ICONS_FOLDER = os.path.join("static", "uploads", "bundle_icons")
            os.makedirs(BUNDLE_ICONS_FOLDER, exist_ok=True)
            
            ext = icon_file.filename.rsplit(".", 1)[-1].lower()
            if ext in {"png", "jpg", "jpeg", "webp", "gif"}:
                stored_name = f"bundle_{id}_{secure_filename(icon_file.filename)}"
                save_path = os.path.join(BUNDLE_ICONS_FOLDER, stored_name)
                icon_file.save(save_path)
                icon_path = f"uploads/bundle_icons/{stored_name}"
        
        # Parse includes (one per line)
        includes = [line.strip() for line in includes_text.split("\n") if line.strip()]
        
        # Validate theme JSON
        try:
            theme = json.loads(theme_json_text)
        except json.JSONDecodeError:
            flash("Invalid theme JSON format.", "danger")
            return redirect(url_for("admin_bundle_edit", id=id))
        
        # Update with or without icon
        if icon_path:
            c.execute("""
                UPDATE bundles
                SET name=?, slug=?, description=?, includes_json=?, theme_json=?, banner_preset=?, is_active=?, min_plan=?, icon_path=?
                WHERE id=?
            """, (name, slug, description, json.dumps(includes), json.dumps(theme), banner_preset, is_active, min_plan, icon_path, id))
        else:
            c.execute("""
                UPDATE bundles
                SET name=?, slug=?, description=?, includes_json=?, theme_json=?, banner_preset=?, is_active=?, min_plan=?
                WHERE id=?
            """, (name, slug, description, json.dumps(includes), json.dumps(theme), banner_preset, is_active, min_plan, id))
        conn.commit()
        conn.close()
        
        flash("Bundle updated successfully.", "success")
        return redirect(url_for("admin_bundles"))
    
    # GET request
    c.execute("""
        SELECT id, slug, name, description, includes_json, theme_json, banner_preset, is_active, min_plan, icon_path
        FROM bundles
        WHERE id = ?
    """, (id,))
    b = c.fetchone()
    
    # Fetch all custom animations for the asset library
    c.execute("SELECT id, animation_type, file_path, name, category, min_plan FROM custom_animations ORDER BY name ASC")
    animations_raw = c.fetchall()
    conn.close()
    
    asset_library = {
        "banner": [],
        "manga_enter": [],
        "login": [],
        "logout": [],
        "avatar_bg": []
    }
    
    for anim in animations_raw:
        a_type = anim[1]
        if a_type in asset_library:
            asset_library[a_type].append({
                "id": anim[0],
                "path": anim[2].replace("\\", "/"), # Normalize for web
                "name": anim[3] or f"Untitled {anim[1]}",
                "category": anim[4],
                "tag": anim[5]
            })
    
    if not b:
        flash("Bundle not found.", "danger")
        return redirect(url_for("admin_bundles"))
    
    bundle = {
        "id": b[0],
        "slug": b[1],
        "name": b[2],
        "description": b[3],
        "includes": json.loads(b[4]) if b[4] else [],
        "theme": json.loads(b[5]) if b[5] else {},
        "banner_preset": b[6],
        "is_active": b[7],
        "min_plan": b[8],
        "icon_path": b[9]
    }
    
    return render_template("admin_bundle_edit.html", bundle=bundle, assets=asset_library)


@app.route("/admin/bundles/create", methods=["POST"])
@admin_required
def admin_bundle_create():
    """Create a new bundle"""
    import json
    
    name = request.form.get("name", "New Bundle").strip()
    slug = request.form.get("slug", "").strip() or name.lower().replace(" ", "-")
    description = request.form.get("description", "New bundle description").strip()
    accent_choice = request.form.get("accentColor", "cyan")
    theme_mode = request.form.get("themeMode", "dark")
    min_plan = request.form.get("minPlan", "basic")
    
    # Accent color mapping
    accent_map = {
        "cyan": ["#0d1117", "#161b22", "#21262d", "#00d4ff", "#58a6ff", "#c9a0dc"],
        "purple": ["#0d1117", "#161b22", "#21262d", "#667eea", "#764ba2", "#c9a0dc"],
        "ruby": ["#0d1117", "#161b22", "#21262d", "#ef4444", "#b91c1c", "#ff9a9e"],
        "emerald": ["#0d1117", "#161b22", "#21262d", "#10b981", "#059669", "#a8e6cf"],
        "amber": ["#0d1117", "#161b22", "#21262d", "#f59e0b", "#d97706", "#ff6b35"]
    }
    
    selected_colors = accent_map.get(accent_choice, accent_map["cyan"])
    
    # Default theme
    default_theme = {
        "theme": theme_mode,
        "accentColor": accent_choice,
        "fontSize": "medium",
        "density": "comfortable",
        "smoothScroll": True,
        "pageTransitions": True,
        "animations": True,
        "uiEffects": True,
        "specialEffects": True,
        "colors": selected_colors
    }
    
    conn = get_conn()
    c = conn.cursor()
    
    try:
        c.execute("""
            INSERT INTO bundles (slug, name, description, includes_json, theme_json, banner_preset, min_plan)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (slug, name, description, json.dumps([]), json.dumps(default_theme), "none", min_plan))
        conn.commit()
        new_id = c.lastrowid
    except sqlite3.IntegrityError:
        conn.close()
        flash("A bundle with this slug already exists.", "danger")
        return redirect(url_for("admin_bundles"))
    
    conn.close()
    flash("Bundle created successfully.", "success")
    return redirect(url_for("admin_bundle_edit", id=new_id))


@app.route("/admin/bundles/<int:id>/delete", methods=["POST"])
@admin_required
def admin_bundle_delete(id):
    """Delete a bundle"""
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM bundles WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    
    flash("Bundle deleted.", "success")
    return redirect(url_for("admin_bundles"))


@app.route("/admin/bundles/<int:id>/toggle", methods=["POST"])
@admin_required
def admin_bundle_toggle(id):
    """Toggle bundle active status"""
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE bundles SET is_active = CASE WHEN is_active = 1 THEN 0 ELSE 1 END WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for("admin_bundles"))


@app.route("/api/bundles")
def api_bundles():
    """API endpoint to get all active bundles as JSON"""
    if "user_id" not in session:
        return jsonify({"error": "login required"}), 401
    
    conn = get_conn()
    c = conn.cursor()
    
    c.execute("""
        SELECT id, slug, name, description, includes_json, theme_json, banner_preset
        FROM bundles
        WHERE is_active = 1
        ORDER BY id
    """)
    bundles_raw = c.fetchall()
    conn.close()
    
    import json
    bundles_list = []
    for b in bundles_raw:
        bundles_list.append({
            "id": b[0],
            "slug": b[1],
            "name": b[2],
            "description": b[3],
            "includes": json.loads(b[4]) if b[4] else [],
            "theme": json.loads(b[5]) if b[5] else {},
            "banner_preset": b[6]
        })
    
    return jsonify({"bundles": bundles_list})


# -------------------- MAIN --------------------


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
            
    
    @app.route('/api/manga/chat', methods=['POST'])
    def chat_manga():
        """
        Chat with AI about a specific manga/chapter
        Body: { manga_id, chapter_id, message, (optional) history }
        """
        if 'user_id' not in session:
            return jsonify({'error': 'login required'}), 401
        
        if not IMAGE_AI_AVAILABLE:
            return jsonify({'error': 'AI chat not available'}), 503
            
        data = request.json
        manga_id = data.get('manga_id')
        chapter_id = data.get('chapter_id')
        message = data.get('message')
        
        if not message:
            return jsonify({'error': 'Message required'}), 400
            
        try:
            conn = get_conn()
            c = conn.cursor()
            
            # Fetch context info (Manga Title, Chapter Name)
            context_text = ""
            if manga_id:
                c.execute("SELECT title, description FROM books WHERE id = ?", (manga_id,))
                book = c.fetchone()
                if book:
                    context_text += f"Manga: {book[0]}\nDescription: {book[1] or 'N/A'}\n"
            
            if chapter_id:
                c.execute("SELECT title, chapter_num FROM chapters WHERE id = ?", (chapter_id,))
                chap = c.fetchone()
                if chap:
                    context_text += f"Current Chapter: {chap[1]} - {chap[0] or ''}\n"
            
            conn.close()
            
            # Call AI
            ai = ImageSummaryAI()
            reply = ai.chat_with_context(message, context_text)
            
            return jsonify({
                'success': True,
                'reply': reply
            })
            
        except Exception as e:
            return jsonify({'error': f'Chat failed: {str(e)}'}), 500

    
    
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
        os.remove(temp_path)
        
        return jsonify({
            'success': True,
            'extracted_text': text
        })
    
    except Exception as e:
        return jsonify({'error': f'Text extraction failed: {str(e)}'}), 500


# ---------- Support / Requests System ----------

@app.route("/support", methods=["GET", "POST"])
def support_requests():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_conn()
    c = conn.cursor()

    if request.method == "POST":
        # Handle New Request Submission
        title = request.form.get("title")
        item_type = request.form.get("item_type")
        author = request.form.get("author")
        notes = request.form.get("notes")
        manga_id = request.form.get("manga_id") or None

        if title and item_type:
            c.execute("""
                INSERT INTO requests (user_id, title, item_type, author, notes, manga_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (session["user_id"], title, item_type, author, notes, manga_id))
            conn.commit()
            flash("Request submitted successfully!", "success")
        else:
            flash("Title and Type are required.", "error")
        
        conn.close()
        return redirect(url_for("support_requests"))

    # GET: Fetch Requests
    filter_type = request.args.get("type", "all") # all, book, manga
    tab = request.args.get("tab", "trending") # trending, newest, my_requests, answered

    query = """
        SELECT r.id, r.title, r.item_type, r.author, r.status, r.vote_count, u.username,
               (SELECT vote_value FROM request_votes WHERE request_id = r.id AND user_id = ?) as user_vote,
               r.manga_id, b.title as manga_title, r.user_id, r.notes,
               f.username as fulfiller_name
        FROM requests r
        JOIN users u ON r.user_id = u.id
        LEFT JOIN books b ON r.manga_id = b.id
        LEFT JOIN users f ON r.fulfilled_by = f.id
        WHERE 1=1
    """
    params = [session["user_id"]]

    if filter_type != "all":
        query += " AND r.item_type = ?"
        params.append(filter_type)

    if tab == "my_requests":
        query += " AND r.user_id = ?"
        params.append(session["user_id"])
    elif tab == "answered":
        query += " AND r.status IN ('Added', 'Rejected', 'Planned')"
    else: # Trending (default) or Newest
        # Show ONLY active requests (Requested)
        query += " AND r.status = 'Requested'"
    
    # Ordering
    if tab == "newest":
        query += " ORDER BY r.created_at DESC"
    else: # Trending (default)
        query += " ORDER BY r.vote_count DESC, r.created_at DESC"

    c.execute(query, tuple(params))
    requests_list = c.fetchall()
    conn.close()

    return render_template("support_requests.html", requests=requests_list, active_tab=tab, active_filter=filter_type)


@app.route("/api/requests/vote", methods=["POST"])
def vote_request():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    request_id = data.get("request_id")
    vote_val = int(data.get("vote_value", 0)) # 1 for upvote, -1 for downvote (or 0 to remove?)

    if not request_id or vote_val not in [1, -1]:
         return jsonify({"error": "Invalid data"}), 400

    conn = get_conn()
    c = conn.cursor()

    try:
        # check existing vote
        c.execute("SELECT vote_value FROM request_votes WHERE request_id=? AND user_id=?", (request_id, session["user_id"]))
        existing = c.fetchone()
        
        current_vote = existing[0] if existing else 0
        
        # logic: if clicking same vote -> remove it (toggle). If different -> update.
        new_vote = vote_val
        if current_vote == vote_val:
            # Toggle off
            c.execute("DELETE FROM request_votes WHERE request_id=? AND user_id=?", (request_id, session["user_id"]))
            new_vote = 0
        else:
            # Insert or Replace
            c.execute("""
                INSERT OR REPLACE INTO request_votes (request_id, user_id, vote_value)
                VALUES (?, ?, ?)
            """, (request_id, session["user_id"], vote_val))
        
        # Recalculate total votes
        c.execute("SELECT SUM(vote_value) FROM request_votes WHERE request_id=?", (request_id,))
        total_votes = c.fetchone()[0] or 0
        
        # Update cache column
        c.execute("UPDATE requests SET vote_count = ? WHERE id = ?", (total_votes, request_id))
        conn.commit()
        
        return jsonify({"success": True, "new_count": total_votes, "user_vote": new_vote})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route("/api/requests/status", methods=["POST"])
def update_request_status():
    if "user_id" not in session or session.get("role") not in ["admin", "publisher"]:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    request_id = data.get("request_id")
    new_status = data.get("status")

    if not request_id or not new_status:
         return jsonify({"error": "Invalid data"}), 400

    conn = get_conn()
    c = conn.cursor()

    try:
        c.execute("UPDATE requests SET status = ? WHERE id = ?", (new_status, request_id))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route("/api/requests/delete", methods=["POST"])
def delete_request():
    if not session.get("user_id"):
        return jsonify({"success": False, "error": "Login required"}), 401
    
    data = request.json
    req_id = data.get("request_id")
    uid = session["user_id"]
    role = session.get("role", "reader")

    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT user_id, status FROM requests WHERE id = ?", (req_id,))
    row = c.fetchone()
    
    if not row:
        conn.close()
        return jsonify({"success": False, "error": "Request not found"}), 404
    
    owner_id, status = row
    
    if status == 'Added':
        conn.close()
        return jsonify({"success": False, "error": "Cannot delete fulfilled requests"}), 403

    # Auth: Admin or Owner (if still requested)
    if role not in ["admin", "publisher"] and (owner_id != uid or status != "Requested"):
        conn.close()
        return jsonify({"success": False, "error": "Unauthorized"}), 403
    
    c.execute("DELETE FROM requests WHERE id = ?", (req_id,))
    c.execute("DELETE FROM request_votes WHERE request_id = ?", (req_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route("/api/requests/edit", methods=["POST"])
def edit_request():
    if not session.get("user_id"):
        return jsonify({"success": False, "error": "Login required"}), 401
    
    data = request.json
    req_id = data.get("request_id")
    uid = session["user_id"]
    role = session.get("role", "reader")

    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT user_id, status FROM requests WHERE id = ?", (req_id,))
    row = c.fetchone()
    
    if not row:
        conn.close()
        return jsonify({"success": False, "error": "Request not found"}), 404
    
    owner_id, status = row

    if status == 'Added':
        conn.close()
        return jsonify({"success": False, "error": "Cannot edit fulfilled requests"}), 403

    if role not in ["admin", "publisher"] and (owner_id != uid or status != "Requested"):
        conn.close()
        return jsonify({"success": False, "error": "Unauthorized"}), 403
    
    title = data.get("title")
    item_type = data.get("item_type")
    author = data.get("author")
    notes = data.get("notes")
    manga_id = data.get("manga_id")

    c.execute("""
        UPDATE requests 
        SET title=?, item_type=?, author=?, notes=?, manga_id=?
        WHERE id=?
    """, (title, item_type, author, notes, manga_id, req_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/admin/revenue")
def admin_revenue():
    if "user_id" not in session:
        return redirect(url_for('login'))
        
    import datetime
    
    conn = get_conn()
    c = conn.cursor()
    
    user_id = session["user_id"]
    
    # Fetch current user details
    c.execute("SELECT plan, role FROM users WHERE id = ?", (user_id,))
    u_row = c.fetchone()
    user_plan = u_row[0] if u_row else 'basic'
    user_role = u_row[1] if u_row else 'user'
    
    # Access Control: Admin, Publisher, or Pro/Ultimate
    if user_role not in ['admin', 'publisher'] and user_plan not in ['pro', 'ultimate']:
         conn.close()
         flash("Access restricted to Pro/Ultimate members or Publishers.", "warning")
         return redirect(url_for('index'))
    
    # Fetch Monetization Request Status
    c.execute("SELECT status FROM role_requests WHERE user_id = ? AND requested_role IN ('monetization', 'publisher') ORDER BY created_at DESC LIMIT 1", (user_id,))
    req_row = c.fetchone()
    monetization_status = req_row[0] if req_row else 'none' # none, pending, approved, rejected
    
    # --- KPI CALCULATIONS ---
    
    # 1. MRR: Sum of monthly value of active subscriptions
    c.execute("SELECT plan, COUNT(*) FROM users WHERE is_banned=0 GROUP BY plan")
    plan_counts = dict(c.fetchall())
    
    pro_users = plan_counts.get('pro', 0)
    ultimate_users = plan_counts.get('ultimate', 0)
    
    mrr_val = (pro_users * 4.99) + (ultimate_users * 9.99)
    # Formatting
    mrr_display = f"${mrr_val:,.2f}"
    
    # 2. Total Revenue: Sum of all completed transactions
    c.execute("SELECT SUM(amount) FROM transactions WHERE status='Completed'")
    total_rev = c.fetchone()[0] or 0.0
    total_rev_display = f"${total_rev:,.2f}"
    
    # 3. ARPU: MRR / Total Active Users (Basic + Pro + Ultimate)
    total_users = plan_counts.get('basic', 0) + pro_users + ultimate_users
    arpu_val = (mrr_val / total_users) if total_users > 0 else 0
    arpu_display = f"${arpu_val:,.2f}"
    
    # 4. Refund Rate: Refunded / Total Transactions
    c.execute("SELECT COUNT(*) FROM transactions")
    total_tx = c.fetchone()[0] or 0
    c.execute("SELECT COUNT(*) FROM transactions WHERE status='Refunded'")
    refunded_tx = c.fetchone()[0] or 0
    
    refund_rate_val = (refunded_tx / total_tx * 100) if total_tx > 0 else 0.0
    refund_rate_display = f"{refund_rate_val:.1f}%"

    # 5. Publisher Earnings (New)
    try:
        c.execute("SELECT SUM(amount) FROM publisher_earnings")
        total_pub_earnings = c.fetchone()[0] or 0.0
    except:
        total_pub_earnings = 0.0
        
    pub_earnings_display = f"${total_pub_earnings:,.2f}"

    # KPI Object
    kpi_data = {
        "total_revenue": {"value": total_rev_display, "delta": "+0.0%", "trend": "neutral"},
        "mrr": {"value": mrr_display, "delta": "+0.0%", "trend": "neutral"},
        "arpu": {"value": arpu_display, "delta": "+0.0%", "trend": "neutral"},
        "refund_rate": {"value": refund_rate_display, "delta": "0.0%", "trend": "neutral"},
        "publisher_earnings": {"value": pub_earnings_display, "delta": "+0.0%", "trend": "positive" if total_pub_earnings > 0 else "neutral"}
    }
    
    # --- TRANSACTIONS ---
    c.execute("""
        SELECT t.created_at, u.username, t.type, t.item, t.amount, t.status, t.invoice_id
        FROM transactions t
        LEFT JOIN users u ON t.user_id = u.id
        ORDER BY t.created_at DESC
        LIMIT 10
    """)
    rows = c.fetchall()
    
    transactions = []
    for r in rows:
        # Format date nicely
        try:
            dt = datetime.datetime.strptime(r[0], "%Y-%m-%d %H:%M:%S")
            date_str = dt.strftime("%b %d, %Y")
        except:
            date_str = r[0]
            
        transactions.append({
            "date": date_str,
            "user": r[1] or "Unknown",
            "type": r[2],
            "item": r[3],
            "amount": f"${r[4]:.2f}",
            "status": r[5],
            "invoice": r[6]
        })

    # --- EARNINGS LOG ---
    earnings = []
    try:
        c.execute("""
            SELECT pe.created_at, r.title, pe.amount, pe.reason
            FROM publisher_earnings pe
            JOIN requests r ON pe.request_id = r.id
            ORDER BY pe.created_at DESC
            LIMIT 5
        """)
        earnings_rows = c.fetchall()
        for er in earnings_rows:
            earnings.append({
                "date": er[0],
                "title": er[1],
                "amount": f"${er[2]:.2f}",
                "reason": er[3]
            })
    except:
        pass
        
    conn.close()

    return render_template(
        "admin_revenue.html", 
        kpi=kpi_data, 
        transactions=transactions, 
        earnings=earnings,
        user_plan=user_plan,
        user_role=user_role,
        monetization_status=monetization_status
    )

@app.route("/api/monetization/request", methods=["POST"])
def request_monetization():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401
        
    conn = get_conn()
    c = conn.cursor()
    
    # Check if already has pending
    print(f"DEBUG: Processing monetization request for user {session.get('user_id')}")
    c.execute("SELECT id FROM role_requests WHERE user_id=? AND requested_role='monetization' AND status='pending'", (session["user_id"],))
    if c.fetchone():
        conn.close()
        return jsonify({"error": "Request already pending"}), 400
        
    c.execute("INSERT INTO role_requests (user_id, requested_role, status) VALUES (?, 'monetization', 'pending')", (session["user_id"],))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True})

@app.route("/admin/users/approve_role", methods=["POST"])
@admin_required
def approve_role_request():
    request_id = request.form.get("request_id")
    action = request.form.get("action") # approve / reject
    
    conn = get_conn()
    c = conn.cursor()
    
    c.execute("SELECT user_id, requested_role FROM role_requests WHERE id = ?", (request_id,))
    req = c.fetchone()
    
    if not req:
        conn.close()
        flash("Request not found", "error")
        return redirect(url_for("user_management"))
        
    user_id, role = req
    
    if action == "approve":
        c.execute("UPDATE role_requests SET status='approved' WHERE id=?", (request_id,))
        # If request is publisher OR monetization, grant publisher role
        if role in ['publisher', 'monetization']:
            c.execute("UPDATE users SET role='publisher' WHERE id=?", (user_id,))
        flash(f"User promoted to publisher via {role} request!", "success")
    else:
        c.execute("UPDATE role_requests SET status='rejected' WHERE id=?", (request_id,))
        flash("Request rejected.", "info")
        
    conn.commit()
    conn.close()
    return redirect(url_for("user_management"))

@app.route("/admin/revenue/export")
@admin_required
def admin_revenue_export():
    import csv
    import io
    from flask import make_response
    
    conn = get_conn()
    c = conn.cursor()
    
    c.execute("""
        SELECT t.id, t.created_at, u.username, u.email, t.type, t.item, t.amount, t.status, t.invoice_id
        FROM transactions t
        LEFT JOIN users u ON t.user_id = u.id
        ORDER BY t.created_at DESC
    """)
    rows = c.fetchall()
    conn.close()
    
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['Transaction ID', 'Date', 'Username', 'Email', 'Type', 'Item', 'Amount', 'Status', 'Invoice ID'])
    cw.writerows(rows)
    
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=revenue_export.csv"
    output.headers["Content-type"] = "text/csv"
    return output


@app.route("/admin/groups/create", methods=["GET", "POST"])
@admin_required
def admin_create_group():
    """Admin page/route for creating new community groups"""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        group_type = request.form.get("group_type", "general")
        
        icon_url = None
        banner_url = None
        
        # Handle file uploads
        UPLOAD_FOLDER = os.path.join("static", "uploads", "groups")
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        if 'icon_file' in request.files:
            icon_file = request.files['icon_file']
            if icon_file and icon_file.filename:
                filename = secure_filename(f"icon_{int(datetime.now().timestamp())}_{icon_file.filename}")
                icon_path = os.path.join(UPLOAD_FOLDER, filename)
                icon_file.save(icon_path)
                icon_url = f"/static/uploads/groups/{filename}"
        
        if 'banner_file' in request.files:
            banner_file = request.files['banner_file']
            if banner_file and banner_file.filename:
                filename = secure_filename(f"banner_{int(datetime.now().timestamp())}_{banner_file.filename}")
                banner_path = os.path.join(UPLOAD_FOLDER, filename)
                banner_file.save(banner_path)
                banner_url = f"/static/uploads/groups/{filename}"
        
        if not name:
            flash("Group name is required", "error")
            return redirect(url_for("admin_create_group"))
        
        conn = get_conn()
        c = conn.cursor()
        
        # Check if group name already exists
        c.execute("SELECT id FROM community_groups WHERE name = ?", (name,))
        if c.fetchone():
            conn.close()
            flash("A group with this name already exists", "error")
            return redirect(url_for("admin_create_group"))
        
        # Insert new group
        c.execute("""
            INSERT INTO community_groups (name, description, group_type, icon_url, banner_url, owner_id, is_auto_created)
            VALUES (?, ?, ?, ?, ?, ?, 0)
        """, (name, description, group_type, icon_url, banner_url, session.get("user_id")))
        
        new_group_id = c.lastrowid
        
        # Auto-join admin to the group as owner
        c.execute("""
            INSERT INTO group_members (group_id, user_id, role)
            VALUES (?, ?, 'owner')
        """, (new_group_id, session.get("user_id")))
        
        # Update member count
        c.execute("UPDATE community_groups SET member_count = 1 WHERE id = ?", (new_group_id,))
        
        conn.commit()
        conn.close()
        
        flash(f"Group '{name}' created successfully!", "success")
        return redirect(url_for("group_page", group_id=new_group_id))
    
    return render_template("admin_create_group.html")

@app.route("/api/bundles/apply", methods=["POST"])
def apply_bundle():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    bundle = data.get("bundle")
    if not bundle:
        return jsonify({"error": "No bundle provided"}), 400
        
    theme = bundle.get("theme", {})
    user_id = session["user_id"]
    
    conn = get_conn()
    c = conn.cursor()
    
    try:
        # Define the mapping of bundle keys to animation types
        # key in bundle.theme -> (animation_type in DB, fallback_style_key)
        mappings = {
            "banner_path": "banner",
            "manga_path": "manga_enter",
            "login_animation": "login",
            "logout_animation": "logout"
        }
        
        for json_key, anim_type in mappings.items():
            path_value = theme.get(json_key)
            
            # Deactivate current active animation for this user/type
            # logic: set all of this type to inactive first
            c.execute("UPDATE custom_animations SET is_active = 0 WHERE user_id = ? AND animation_type = ?", (user_id, anim_type))
            
            if path_value:
                # It's a file path. Activate or Insert.
                
                # First, verify if the path refers to a "system" file or user file.
                # Actually, we just need a record in custom_animations pointing to it.
                
                # Check if this exact path exists for this user as a record
                c.execute("SELECT id FROM custom_animations WHERE user_id = ? AND file_path = ? AND animation_type = ?", (user_id, path_value, anim_type))
                existing = c.fetchone()
                
                if existing:
                    c.execute("UPDATE custom_animations SET is_active = 1 WHERE id = ?", (existing[0],))
                else:
                    # check if it exists as a "preset" (user_id IS NULL or special flag?)
                    # If not, just insert a new record for this user.
                    # Name can be from bundle name or generic.
                    name = f"Bundle: {bundle.get('name', 'Unknown')}"
                    c.execute("""
                        INSERT INTO custom_animations (user_id, animation_type, file_path, is_active, name, category)
                        VALUES (?, ?, ?, 1, ?, 'animation')
                    """, (user_id, anim_type, path_value, name))
                
        conn.commit()
        return jsonify({"success": True})
        
    except Exception as e:
        # print(f"Bundle apply error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


# --- Community Reviews API ---

@app.route("/api/reviews/post", methods=["POST"])
def api_post_review():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    book_title = data.get("title")
    rating = data.get("rating")
    body = data.get("body")
    has_spoilers = data.get("hasSpoilers")
    status = data.get("status")
    
    if not book_title or not body:
        return jsonify({"error": "Missing required fields"}), 400
        
    conn = get_conn()
    c = conn.cursor()
    
    # Try to find book_id by title
    c.execute("SELECT id FROM books WHERE title = ?", (book_title,))
    book = c.fetchone()
    if not book:
        conn.close()
        return jsonify({"error": "Book not found"}), 404
    book_id = book[0]
    
    c.execute("""
        INSERT INTO reviews (user_id, book_id, rating, content, has_spoilers, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (session["user_id"], book_id, rating, body, has_spoilers, status))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True})

@app.route("/api/reviews/update", methods=["POST"])
def api_update_review():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    review_id = data.get("reviewId")
    rating = data.get("rating")
    body = data.get("body")
    has_spoilers = data.get("hasSpoilers")
    status = data.get("status")
    
    if not all([review_id, rating, body, status]):
        return jsonify({"error": "Missing required fields"}), 400
        
    conn = get_conn()
    c = conn.cursor()
    
    # Verify ownership
    c.execute("SELECT user_id FROM reviews WHERE id = ?", (review_id,))
    review = c.fetchone()
    if not review:
        conn.close()
        return jsonify({"error": "Review not found"}), 404
    if str(review[0]) != str(session["user_id"]):
        conn.close()
        return jsonify({"error": "Unauthorized"}), 403
        
    c.execute("""
        UPDATE reviews 
        SET rating = ?, content = ?, has_spoilers = ?, status = ?
        WHERE id = ?
    """, (rating, body, has_spoilers, status, review_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({"success": True})

@app.route("/api/reviews/like", methods=["POST"])
def api_like_review():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    review_id = data.get("reviewId")
    
    if not review_id:
        return jsonify({"error": "Missing reviewId"}), 400
        
    conn = get_conn()
    c = conn.cursor()
    
    # Check if already liked
    c.execute("SELECT 1 FROM review_likes WHERE user_id = ? AND review_id = ?", (session["user_id"], review_id))
    already_liked = c.fetchone()
    
    if already_liked:
        # Toggle: unlike
        c.execute("DELETE FROM review_likes WHERE user_id = ? AND review_id = ?", (session["user_id"], review_id))
        action = "unliked"
    else:
        # Like
        c.execute("INSERT INTO review_likes (user_id, review_id) VALUES (?, ?)", (session["user_id"], review_id))
        action = "liked"
        
    conn.commit()
    conn.close()
    return jsonify({"success": True, "action": action})

@app.route("/api/reviews/comments/like", methods=["POST"])
def api_like_comment():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    comment_id = data.get("commentId")
    
    if not comment_id:
        return jsonify({"error": "Missing commentId"}), 400
        
    conn = get_conn()
    c = conn.cursor()
    
    # Check if already liked
    c.execute("SELECT 1 FROM comment_likes WHERE user_id = ? AND comment_id = ?", (session["user_id"], comment_id))
    already_liked = c.fetchone()
    
    if already_liked:
        # Toggle: unlike
        c.execute("DELETE FROM comment_likes WHERE user_id = ? AND comment_id = ?", (session["user_id"], comment_id))
        action = "unliked"
    else:
        # Like
        c.execute("INSERT INTO comment_likes (user_id, comment_id) VALUES (?, ?)", (session["user_id"], comment_id))
        action = "liked"
        
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "action": action})

@app.route("/api/reviews/comment", methods=["POST"])
def api_post_comment():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    review_id = data.get("reviewId")
    parent_id = data.get("parentId") # Can be NULL
    content = data.get("content")
    
    if not review_id or not content:
        return jsonify({"error": "Missing fields"}), 400
        
    conn = get_conn()
    c = conn.cursor()
    
    c.execute("""
        INSERT INTO review_comments (user_id, review_id, parent_id, content)
        VALUES (?, ?, ?, ?)
    """, (session["user_id"], review_id, parent_id, content))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True})

@app.route("/api/media/search")
def api_media_search():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify([])
    
    conn = get_conn()
    c = conn.cursor()
    
    c.execute("""
        SELECT id, title, cover_path, book_type, category
        FROM books
        WHERE title LIKE ?
        LIMIT 10
    """, (f"%{query}%",))
    books_raw = c.fetchall()
    conn.close()
    
    results = []
    for b in books_raw:
        cover_path = b[2]
        if cover_path and not cover_path.startswith(('http://', 'https://')):
            cover_url = f"/static/{cover_path}"
        else:
            cover_url = cover_path or 'https://picsum.photos/seed/cs/200/300'
            
        results.append({
            "id": str(b[0]),
            "title": b[1],
            "coverUrl": cover_url,
            "type": (b[3] or 'BOOK').upper(),
            "tags": [t.strip() for t in b[4].split(',')] if b[4] else []
        })
    return jsonify(results)

@app.route('/ranking')
def ranking():
    """Ranking page for manga and books"""
    conn = get_conn()
    c = conn.cursor()
    
    # Fetch all books with their view counts
    c.execute("""
        SELECT 
            b.id,
            b.title,
            b.author,
            b.description,
            b.cover_path,
            b.book_type,
            COALESCE(COUNT(DISTINCT mp.user_id), 0) as total_views
        FROM books b
        LEFT JOIN manga_progress mp ON b.id = mp.manga_id
        GROUP BY b.id
        ORDER BY total_views DESC
    """)
    
    books_data = c.fetchall()
    
    # Get user's favorites if logged in
    user_id = session.get("user_id")
    favorited_book_ids = set()
    if user_id:
        c.execute("SELECT book_id FROM favorites WHERE user_id = ?", (user_id,))
        favorited_book_ids = {row[0] for row in c.fetchall()}
        
    conn.close()
    
    items = []
    manga_rank = {'Hottest': 0, 'Trending': 0, 'Most Popular': 0, 'Ongoing': 0, 'Completed': 0, 'Most Viewed': 0}
    book_rank = {'Hottest': 0, 'Trending': 0, 'Most Popular': 0, 'Fiction': 0, 'Non-Fiction': 0, 'Most Viewed': 0}
    
    for idx, book in enumerate(books_data):
        book_id, title, author, description, cover_path, book_type, views = book
        
        # Determine type (Manga or Book)
        item_type = 'Manga' if book_type and book_type.upper() in ['MANGA', 'MANHWA', 'MANHUA'] else 'Book'
        
        # Determine categories based on views
        categories = []
        
        # Add category based on views (top items are "Hottest" and "Most Viewed")
        if idx < 10:  # Top 10 are hottest
            categories.append('Hottest')
        if idx < 5:  # Top 5 are trending
            categories.append('Trending')
        if views > 10:  # High view count = Most Popular
            categories.append('Most Popular')
        
        # Always add Most Viewed category
        categories.append('Most Viewed')
        
        # Add default categories based on type
        if item_type == 'Manga':
            # Default to Ongoing for manga (can be updated later with a status column)
            categories.append('Ongoing')
        else:
            # Default to Fiction for books
            categories.append('Fiction')
        
        # Determine rank for each category
        rank_dict = manga_rank if item_type == 'Manga' else book_rank
        for cat in categories:
            if cat in rank_dict:
                rank_dict[cat] += 1
        
        # Use the first category's rank as the primary rank
        primary_category = categories[0] if categories else 'Hottest'
        rank = rank_dict.get(primary_category, idx + 1)
        
        # Handle cover image path
        if cover_path:
            if cover_path.startswith(('http://', 'https://')):
                image_url = cover_path
            else:
                image_url = f"/static/{cover_path}"
        else:
            # Fallback to placeholder
            image_url = f"https://picsum.photos/seed/{book_id}/400/600"
        
        # Default description if none exists
        if not description:
            description = f"Discover the story of {title} by {author or 'Unknown Author'}."
        
        # Languages - default to English for now (can be extended with a languages column)
        languages = ['EN']
        
        items.append({
            'id': book_id,
            'rank': rank,
            'title': title or 'Untitled',
            'author': author or 'Unknown Author',
            'description': description[:200] if description else '',  # Limit description length
            'views': int(views) if views else 0,
            'imageUrl': image_url,
            'languages': languages,
            'type': item_type,
            'categories': categories,
            'is_favorited': book_id in favorited_book_ids
        })
    
    return render_template('ranking.html', items=items)


@app.route("/api/manga/search")
def api_manga_search():
    query = request.args.get("q", "").strip()
    
    conn = get_conn()
    c = conn.cursor()
    
    if query:
        # Search with query - replace dashes with spaces for #@ shortcut support
        search_term = query.replace('-', ' ')
        c.execute("""
            SELECT id, title, author, cover_path 
            FROM books 
            WHERE (book_type = 'manga' OR category LIKE '%Manga%')
            AND title LIKE ? 
            LIMIT 10
        """, (f"%{search_term}%",))
    else:
        # Return recent/popular manga when no query
        c.execute("""
            SELECT id, title, author, cover_path 
            FROM books 
            WHERE (book_type = 'manga' OR category LIKE '%Manga%')
            ORDER BY id DESC
            LIMIT 10
        """)
    
    rows = c.fetchall()
    conn.close()
    
    results = []
    for row in rows:
        cover = row[3]
        # Ensure cover path is a proper URL
        if cover and not cover.startswith('http') and not cover.startswith('/'):
            cover = f'/static/{cover}'
        elif not cover:
            cover = 'https://via.placeholder.com/200x300?text=No+Cover'
        
        results.append({
            'id': row[0],
            'title': row[1],
            'author': row[2] or 'Unknown',
            'cover': cover
        })
    return jsonify(results)


@app.route("/api/users/search")
@login_required
def api_users_search():
    """Search users for @ mentions"""
    query = request.args.get("q", "").strip().lower()
    group_id = request.args.get("group_id")
    
    conn = get_conn()
    c = conn.cursor()
    
    results = []
    
    # Special mention targets
    special_mentions = [
        {'id': 'everyone', 'username': 'everyone', 'type': 'special', 'description': 'Notify all group members'},
        {'id': 'admin', 'username': 'admin', 'type': 'role', 'description': 'All admins'},
        {'id': 'publisher', 'username': 'publisher', 'type': 'role', 'description': 'All publishers'},
        {'id': 'mod', 'username': 'mod', 'type': 'role', 'description': 'All moderators'},
    ]
    
    # Filter special mentions based on query
    for sm in special_mentions:
        if not query or query in sm['username']:
            results.append(sm)
    
    # Search actual users
    if query:
        if group_id:
            c.execute("""
                SELECT u.id, u.username, u.avatar_url, u.role
                FROM users u
                JOIN group_members gm ON u.id = gm.user_id
                WHERE gm.group_id = ? AND u.username LIKE ? 
                ORDER BY u.username
                LIMIT 8
            """, (group_id, f"%{query}%"))
        else:
            c.execute("""
                SELECT id, username, avatar_url, role
                FROM users
                WHERE username LIKE ? 
                ORDER BY username
                LIMIT 8
            """, (f"%{query}%",))
    else:
        # Show recent/active users if no query
        if group_id:
            c.execute("""
                SELECT u.id, u.username, u.avatar_url, u.role
                FROM users u
                JOIN group_members gm ON u.id = gm.user_id
                WHERE gm.group_id = ?
                ORDER BY u.id DESC
                LIMIT 8
            """, (group_id,))
        else:
            c.execute("""
                SELECT id, username, avatar_url, role
                FROM users
                ORDER BY id DESC
                LIMIT 8
            """)
    
    for row in c.fetchall():
        u_id, username, avatar, role = row
        
        # Add basic user result
        results.append({
            'id': u_id,
            'username': username,
            'avatar': avatar,
            'role': role,
            'type': 'user'
        })
        
        # If searching for mod- specifically or user is a moderator/admin, add mod- suggestion
        is_mod_role = role and role.lower() in ['mod', 'moderator', 'admin']
        if (query and query.startswith('mod-')) or is_mod_role:
            results.append({
                'id': f'mod-{u_id}',
                'username': f'mod-{username}',
                'avatar': avatar,
                'role': 'Moderator',
                'type': 'role',
                'description': f'Moderator: {username}'
            })
    
    conn.close()
    return jsonify(results)



# -------------------- COMMUNITY & GROUPS --------------------

def create_group_for_content(title, description, group_type, reference_id=None, category=None, owner_id=None, icon_url=None):
    """Helper function to auto-create a group for manga/book or genre"""
    conn = get_conn()
    c = conn.cursor()
    
    # Check if group already exists for this content
    if reference_id:
        c.execute("SELECT id FROM community_groups WHERE reference_id = ? AND group_type = ?", (reference_id, group_type))
    elif category:
        # Check by category OR name for genre groups to avoid duplicates
        c.execute("SELECT id FROM community_groups WHERE (category = ? OR name = ?) AND group_type = 'genre'", (category, category))
    else:
        c.execute("SELECT id FROM community_groups WHERE name = ? AND group_type = ?", (title, group_type))
    
    existing = c.fetchone()
    if existing:
        conn.close()
        return existing[0]
    
    # Create new group
    banner_url = f"https://picsum.photos/seed/{title.replace(' ', '-').lower()}/1200/300"
    c.execute("""
        INSERT INTO community_groups (name, description, group_type, reference_id, category, owner_id, icon_url, banner_url, is_auto_created)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
    """, (title, description, group_type, reference_id, category, owner_id, icon_url, banner_url))
    
    group_id = c.lastrowid
    
    # If owner specified, add them as owner member
    if owner_id:
        c.execute("""
            INSERT INTO group_members (group_id, user_id, role) VALUES (?, ?, 'owner')
        """, (group_id, owner_id))
    
    conn.commit()
    conn.close()
    return group_id


def ensure_genre_group(genre_name):
    """Ensure a genre group exists, create if not"""
    if not genre_name:
        return None
    description = f"Discuss your favorite {genre_name} manga and anime!"
    return create_group_for_content(genre_name, description, 'genre', category=genre_name)


def get_user_group_role(group_id, user_id):
    """Get user's role in a group"""
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT role FROM group_members WHERE group_id = ? AND user_id = ?", (group_id, user_id))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None


def can_edit_group_settings(group_id, user_id, is_admin):
    """Check if user can edit group settings - owner or site admin"""
    if is_admin:
        return True
    
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT owner_id FROM community_groups WHERE id = ?", (group_id,))
    group = c.fetchone()
    conn.close()
    
    if not group:
        return False
    
    # Owner can edit
    return group[0] == user_id


def sync_community_groups():
    """Ensure all genres and mangas have community groups"""
    try:
        conn = get_conn()
        c = conn.cursor()
        
        # 1. Sync Genre Groups (from books table categories)
        c.execute("SELECT DISTINCT category FROM books")
        raw_categories = [row[0] for row in c.fetchall() if row[0]]
        genres = set()
        for cat_str in raw_categories:
            for cat in cat_str.split(','):
                cleaned = cat.strip()
                if cleaned:
                    genres.add(cleaned)
        
        for genre in genres:
            ensure_genre_group(genre)
            
        # 2. Sync Manga Groups (for each manga entry)
        c.execute("SELECT id, title, description, cover_path FROM books WHERE book_type = 'manga'")
        mangas = c.fetchall()
        for m_id, m_title, m_desc, m_cover in mangas:
            create_group_for_content(
                title=f"{m_title}",
                description=m_desc or f"Official discussion group for {m_title}",
                group_type='manga',
                reference_id=m_id,
                icon_url=m_cover
            )
        
        conn.commit()
        conn.close()
        logger.info("Successfully synced community groups for all genres and mangas")
    except Exception as e:
        if 'logger' in globals():
            logger.error(f"Error syncing community groups: {e}")
        else:
            print(f"Error syncing community groups: {e}")


def get_enriched_posts(c, user_id, raw_rows):
    """Enrich raw post rows with user votes, attachments, and polls"""
    posts = []
    for row in raw_rows:
        post = dict(row)
        post_id = post['id']
        
        # Fetch user vote status
        c.execute("SELECT vote FROM group_post_votes WHERE post_id = ? AND user_id = ?", (post_id, user_id))
        vote_row = c.fetchone()
        post['user_vote'] = vote_row['vote'] if vote_row else 0
        
        # Fetch attachments
        c.execute("SELECT file_url, file_type, file_name FROM group_post_attachments WHERE post_id = ?", (post_id,))
        attachments = []
        for a_row in c.fetchall():
            attach = dict(a_row)
            # If it's a manga link, fetch details
            if attach['file_type'] == 'manga_link':
                try:
                    m_id = attach['file_url'].split('/')[-1]
                    c.execute("SELECT title, cover_path FROM books WHERE id = ?", (m_id,))
                    m_data = c.fetchone()
                    if m_data:
                        attach['manga_title'] = m_data['title']
                        m_cover = m_data['cover_path']
                        if m_cover and not m_cover.startswith('http') and not m_cover.startswith('/'):
                            m_cover = f'/static/{m_cover}'
                        attach['manga_cover'] = m_cover or 'https://via.placeholder.com/200x300?text=No+Cover'
                except: pass
            attachments.append(attach)
        post['attachments'] = attachments
        
        # Fetch poll data
        if post['post_type'] == 'poll':
            c.execute("SELECT id, question, allow_multiple FROM group_polls WHERE post_id = ?", (post_id,))
            poll_row = c.fetchone()
            if poll_row:
                poll = dict(poll_row)
                c.execute("""
                    SELECT id, option_text, vote_count 
                    FROM group_poll_options 
                    WHERE poll_id = ?
                """, (poll['id'],))
                poll['options'] = [dict(opt) for opt in c.fetchall()]
                poll['total_votes'] = sum(opt['vote_count'] for opt in poll['options'])
                
                # User's specific vote
                c.execute("SELECT option_id FROM group_poll_votes WHERE poll_id = ? AND user_id = ?", (poll['id'], user_id))
                poll['user_votes'] = [v['option_id'] for v in c.fetchall()]
                post['poll'] = poll
        
        posts.append(post)
    return posts


@app.route('/community')
@login_required
def community():
    """NOVUS Community page - social hub for discussions and groups"""
    try:
        conn = get_conn()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        user_id = session.get('user_id')
        search_query = request.args.get('q', '').strip()
        
        # Get active groups (Top 3 by member count) [NEW]
        c.execute("""
            SELECT id, name, icon_url, member_count, group_type
            FROM community_groups 
            WHERE group_type != 'system'
            ORDER BY member_count DESC
            LIMIT 3
        """)
        active_groups = [dict(row) for row in c.fetchall()]
        
        # Get user's groups
        c.execute("""
            SELECT cg.id, cg.name, cg.group_type, cg.icon_url, cg.member_count
            FROM community_groups cg
            JOIN group_members gm ON cg.id = gm.group_id
            WHERE gm.user_id = ?
            ORDER BY gm.joined_at DESC
            LIMIT 10
        """, (user_id,))
        my_groups = [dict(row) for row in c.fetchall()]

        # World/Global group is already in my_groups because membership is mandatory.
        # Ensure it's at the top if present
        world_idx = next((i for i, g in enumerate(my_groups) if g['name'] == 'World' and g['group_type'] == 'system'), None)
        if world_idx is not None:
            world_group = my_groups.pop(world_idx)
            my_groups.insert(0, world_group)
        else:
            # Fallback if not joined for some reason
            c.execute("SELECT id, name, group_type, icon_url, member_count FROM community_groups WHERE name = 'World' AND group_type = 'system'")
            world_row = c.fetchone()
            if world_row:
                world_group = dict(world_row)
                world_group['icon_url'] = None 
                my_groups.insert(0, world_group)
        
        # Get suggested groups (groups user hasn't joined)
        c.execute("""
            SELECT id, name, group_type, icon_url, member_count
            FROM community_groups 
            WHERE id NOT IN (SELECT group_id FROM group_members WHERE user_id = ?)
            ORDER BY member_count DESC
            LIMIT 30
        """, (user_id,))
        suggested_groups = [dict(row) for row in c.fetchall()]
        
        # Get recent posts from all groups with detailed info
        query = """
            SELECT gp.id, gp.title, gp.content, gp.post_type, gp.upvotes, gp.downvotes, gp.comment_count, gp.created_at,
                   u.id as user_id, u.username, u.avatar_url as avatar,
                   cg.id as group_id, cg.name as group_name
            FROM group_posts gp
            JOIN users u ON gp.user_id = u.id
            JOIN community_groups cg ON gp.group_id = cg.id
        """
        params = []
        if search_query:
            query += " WHERE (gp.title LIKE ? OR gp.content LIKE ?)"
            params = [f'%{search_query}%', f'%{search_query}%']
            
        query += " ORDER BY RANDOM() LIMIT 30"
        c.execute(query, params)
        
        posts = get_enriched_posts(c, user_id, c.fetchall())
            
        # Get top contributors
        c.execute("""
            SELECT u.id, u.username as name, u.avatar_url as avatar, COUNT(gp.id) as post_count
            FROM users u
            JOIN group_posts gp ON u.id = gp.user_id
            GROUP BY u.id
            ORDER BY post_count DESC
            LIMIT 3
        """)
        top_contributors = [dict(row) for row in c.fetchall()]

        # Recent User Activity (Last 5 posts by current user)
        c.execute("""
            SELECT u.username, gp.title, cg.name as group_name, gp.created_at, gp.post_type
            FROM group_posts gp
            JOIN users u ON gp.user_id = u.id
            JOIN community_groups cg ON gp.group_id = cg.id
            WHERE gp.user_id = ?
            ORDER BY gp.created_at DESC
            LIMIT 5
        """, (user_id,))
        recent_activity = [dict(row) for row in c.fetchall()]

        # Get all genre/manga groups for the browse modal
        c.execute("SELECT id, name, icon_url, member_count FROM community_groups WHERE group_type = 'genre' ORDER BY name ASC")
        all_genre_groups = [dict(row) for row in c.fetchall()]
        
        c.execute("SELECT id, name, icon_url, member_count FROM community_groups WHERE group_type = 'manga' ORDER BY member_count DESC")
        all_manga_groups = [dict(row) for row in c.fetchall()]
        
        # Extract trending hashtags from recent posts
        c.execute("SELECT content FROM group_posts ORDER BY created_at DESC LIMIT 200")
        all_content = ' '.join([row[0] or '' for row in c.fetchall()])
        hashtag_pattern = re.compile(r'#([a-zA-Z0-9_-]+)')
        hashtags = hashtag_pattern.findall(all_content)
        hashtag_counts = Counter(hashtags)
        trending_hashtags = [{'tag': tag, 'count': count} for tag, count in hashtag_counts.most_common(5)]
        
        conn.close()
        
        return render_template('community.html', 
                             my_groups=my_groups, 
                             suggested_groups=suggested_groups,
                             posts=posts,
                             top_contributors=top_contributors,
                             recent_activity=recent_activity,
                             all_genre_groups=all_genre_groups,
                             all_manga_groups=all_manga_groups,
                             active_groups=active_groups,
                             trending_hashtags=trending_hashtags,
                             search_query=search_query)
    except Exception as e:
        logger.error(f"Community page error: {e}")
        # Fallback - render template with empty data
        return render_template('community.html', 
                             my_groups=[], 
                             suggested_groups=[],
                             posts=[],
                             top_contributors=[])


@app.route('/api/community/posts/more')
def api_get_more_posts():
    """API endpoint for infinite scroll - returns more random posts"""
    try:
        user_id = session.get('user_id')
        seen_ids = request.args.getlist('seen[]')
        search_query = request.args.get('q', '').strip()
        
        conn = get_conn()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        query = """
            SELECT gp.id, gp.title, gp.content, gp.post_type, gp.upvotes, gp.downvotes, gp.comment_count, gp.created_at,
                   u.id as user_id, u.username, u.avatar_url as avatar,
                   cg.id as group_id, cg.name as group_name
            FROM group_posts gp
            JOIN users u ON gp.user_id = u.id
            JOIN community_groups cg ON gp.group_id = cg.id
        """
        conditions = []
        params = []
        
        if seen_ids:
            # Sanitize IDs to be integers
            seen_ids = [int(i) for i in seen_ids if str(i).isdigit()]
            if seen_ids:
                placeholders = ', '.join(['?'] * len(seen_ids))
                conditions.append(f"gp.id NOT IN ({placeholders})")
                params.extend(seen_ids)
        
        if search_query:
            conditions.append("(gp.title LIKE ? OR gp.content LIKE ?)")
            params.extend([f'%{search_query}%', f'%{search_query}%'])
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY RANDOM() LIMIT 10"
        c.execute(query, params)
        
        raw_rows = c.fetchall()
        posts = get_enriched_posts(c, user_id, raw_rows)
        conn.close()
        
        if not posts:
            return "" # No more posts
            
        html = ""
        for post in posts:
            html += render_template('post_card_partial.html', post=post)
            
        return html
    except Exception as e:
        logger.error(f"Error fetching more posts: {e}")
        return str(e), 500


@app.route('/group/<int:group_id>')
@login_required
def group_page(group_id):
    """Individual group page"""
    try:
        conn = get_conn()
        c = conn.cursor()
        
        # Get group details
        c.execute("""
            SELECT id, name, description, group_type, reference_id, category, 
                   icon_url, banner_url, owner_id, member_count, post_count, created_at
            FROM community_groups WHERE id = ?
        """, (group_id,))
        row = c.fetchone()
        
        if not row:
            conn.close()
            flash('Group not found', 'error')
            return redirect(url_for('community'))
        
        group = dict(zip(['id', 'name', 'description', 'group_type', 'reference_id', 'category',
                          'icon_url', 'banner_url', 'owner_id', 'member_count', 'post_count', 'created_at'], row))
        
        # Check if current user is a member
        user_id = session.get('user_id')
        c.execute("SELECT role FROM group_members WHERE group_id = ? AND user_id = ?", (group_id, user_id))
        member_row = c.fetchone()
        is_member = member_row is not None
        user_role = member_row[0] if member_row else None
        
        # Site admins are treated as owners of all groups
        if session.get('role') == 'admin':
            user_role = 'owner'
            is_member = True
        
        # Publishers are treated as owners of their manga's groups
        elif group['group_type'] == 'manga' and group['reference_id']:
            c.execute("SELECT uploader_id FROM manga WHERE id = ?", (group['reference_id'],))
            manga_row = c.fetchone()
            if manga_row and manga_row[0] == user_id:
                user_role = 'owner'
                is_member = True
        
        # Check if user can edit settings
        is_admin = session.get('role') == 'admin'
        can_edit_settings = can_edit_group_settings(group_id, user_id, is_admin)
        
        # Get group admins/moderators
        c.execute("""
            SELECT u.id, u.username, u.avatar_url, gm.role
            FROM group_members gm
            JOIN users u ON gm.user_id = u.id
            WHERE gm.group_id = ? AND gm.role IN ('owner', 'admin', 'moderator')
            ORDER BY CASE gm.role WHEN 'owner' THEN 1 WHEN 'admin' THEN 2 ELSE 3 END
        """, (group_id,))
        admins = [dict(zip(['id', 'name', 'avatar', 'role'], row)) for row in c.fetchall()]
        
        # Get recent members
        c.execute("""
            SELECT u.id, u.username, u.avatar_url
            FROM group_members gm
            JOIN users u ON gm.user_id = u.id
            WHERE gm.group_id = ?
            ORDER BY gm.joined_at DESC
            LIMIT 8
        """, (group_id,))
        recent_members = [dict(zip(['id', 'name', 'avatar'], row)) for row in c.fetchall()]
        
        # Get group posts
        c.execute("""
            SELECT gp.id, gp.title, gp.content, gp.post_type, gp.upvotes, gp.downvotes, gp.comment_count, gp.created_at,
                   u.id as user_id, u.username, u.avatar_url, gp.channel_id
            FROM group_posts gp
            JOIN users u ON gp.user_id = u.id
            WHERE gp.group_id = ?
            ORDER BY gp.created_at DESC
            LIMIT 20
        """, (group_id,))
        posts = []
        for r in c.fetchall():
            p_obj = dict(zip(['id', 'title', 'content', 'post_type', 'upvotes', 'downvotes', 'comment_count', 'created_at',
                               'user_id', 'username', 'avatar', 'channel_id'], r))
            # Get attachments
            c.execute("SELECT file_url, file_type, file_name FROM group_post_attachments WHERE post_id = ?", (p_obj['id'],))
            attachments = []
            for row in c.fetchall():
                a_url, a_type, a_name = row
                attach = {'url': a_url, 'type': a_type, 'name': a_name}
                
                # If it's a manga link, try to fetch cover and title
                if a_type == 'manga_link' and '/manga/detail/' in a_url:
                    try:
                        m_id = a_url.split('/')[-1]
                        c.execute("SELECT title, cover_path FROM books WHERE id = ?", (m_id,))
                        m_row = c.fetchone()
                        if m_row:
                            attach['manga_title'] = m_row[0]
                            m_cover = m_row[1]
                            if m_cover and not m_cover.startswith('http') and not m_cover.startswith('/'):
                                m_cover = f'/static/{m_cover}'
                            attach['manga_cover'] = m_cover or 'https://via.placeholder.com/200x300?text=No+Cover'
                    except:
                        pass
                attachments.append(attach)
            p_obj['attachments'] = attachments

            # Fetch poll data if post_type is poll
            if p_obj['post_type'] == 'poll':
                c.execute("""
                    SELECT id, question, allow_multiple, expires_at 
                    FROM group_polls WHERE post_id = ?
                """, (p_obj['id'],))
                poll_row = c.fetchone()
                if poll_row:
                    poll = dict(zip(['id', 'question', 'allow_multiple', 'expires_at'], poll_row))
                    c.execute("""
                        SELECT id, option_text, (SELECT COUNT(*) FROM group_poll_votes WHERE option_id = gpo.id) as votes
                        FROM group_poll_options gpo WHERE poll_id = ?
                    """, (poll['id'],))
                    poll['options'] = [dict(zip(['id', 'text', 'votes'], row)) for row in c.fetchall()]
                    poll['total_votes'] = sum(opt['votes'] for opt in poll['options'])
                    
                    # User's current votes
                    c.execute("SELECT option_id FROM group_poll_votes WHERE poll_id = ? AND user_id = ?", (poll['id'], user_id))
                    poll['user_votes'] = [row[0] for row in c.fetchall()]
                    
                    p_obj['poll'] = poll

            posts.append(p_obj)
        
        # Get related groups (same type or category)
        c.execute("""
            SELECT id, name, icon_url, member_count, group_type
            FROM community_groups
            WHERE id != ? AND (group_type = ? OR category = ?)
            ORDER BY member_count DESC
            LIMIT 3
        """, (group_id, group['group_type'], group.get('category')))
        related_groups = [dict(zip(['id', 'name', 'icon_url', 'member_count', 'group_type'], row)) for row in c.fetchall()]
        
        # Get channels for this group
        c.execute("""
            SELECT id, name, description, channel_type, icon, position
            FROM group_channels
            WHERE group_id = ?
            ORDER BY position ASC
        """, (group_id,))
        channels = [dict(zip(['id', 'name', 'description', 'type', 'icon', 'position'], row)) for row in c.fetchall()]
        
        # Add user vote status to posts
        for post in posts:
            c.execute("SELECT vote FROM group_post_votes WHERE post_id = ? AND user_id = ?", (post['id'], user_id))
            vote_row = c.fetchone()
            post['user_vote'] = vote_row[0] if vote_row else 0
        
        conn.close()
        
        return render_template('group.html', 
                             group=group, 
                             is_member=is_member,
                             user_role=user_role,
                             can_edit_settings=can_edit_settings,
                             admins=admins,
                             recent_members=recent_members,
                             posts=posts,
                             related_groups=related_groups,
                             channels=channels)
    except Exception as e:
        import traceback
        error_msg = f"Group page error for group {group_id}: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Full traceback: {traceback.format_exc()}")
        flash(f'Error loading group: {str(e)}', 'error')
        return redirect(url_for('community'))


@app.route('/group/<int:group_id>/join', methods=['POST'])
@login_required
def join_group(group_id):
    """Join a community group"""
    user_id = session.get('user_id')
    conn = get_conn()
    c = conn.cursor()
    
    # Check if already a member
    c.execute("SELECT id FROM group_members WHERE group_id = ? AND user_id = ?", (group_id, user_id))
    if c.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': 'Already a member'})
    
    # Add member
    c.execute("INSERT INTO group_members (group_id, user_id, role) VALUES (?, ?, 'member')", (group_id, user_id))
    
    # Update member count
    c.execute("UPDATE community_groups SET member_count = member_count + 1 WHERE id = ?", (group_id,))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Joined group successfully'})


@app.route('/group/<int:group_id>/leave', methods=['POST'])
@login_required
def leave_group(group_id):
    """Leave a community group"""
    user_id = session.get('user_id')
    conn = get_conn()
    c = conn.cursor()
    
    # Block leaving World group
    c.execute("SELECT name, group_type FROM community_groups WHERE id = ?", (group_id,))
    g_info = c.fetchone()
    if g_info and g_info[0] == 'World' and g_info[1] == 'system':
        conn.close()
        return jsonify({'success': False, 'message': 'You cannot leave the World group'})
    
    # Check if user is owner
    c.execute("SELECT role FROM group_members WHERE group_id = ? AND user_id = ?", (group_id, user_id))
    result = c.fetchone()
    if result and result[0] == 'owner':
        conn.close()
        return jsonify({'success': False, 'message': 'Owners cannot leave their group'})
    
    # Remove member
    c.execute("DELETE FROM group_members WHERE group_id = ? AND user_id = ?", (group_id, user_id))
    
    # Update member count
    c.execute("UPDATE community_groups SET member_count = member_count - 1 WHERE id = ? AND member_count > 0", (group_id,))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Left group successfully'})


@app.route('/group/<int:group_id>/upload-icon', methods=['POST'])
@login_required
def upload_group_icon(group_id):
    """Upload community group icon"""
    user_id = session.get('user_id')
    is_admin = session.get('role') == 'admin'
    
    if not can_edit_group_settings(group_id, user_id, is_admin):
        return jsonify({'success': False, 'message': 'You do not have permission to edit this group'})
    
    file = request.files.get('file')
    if not file or not file.filename:
        return jsonify({'success': False, 'message': 'No file uploaded'})
    
    from werkzeug.utils import secure_filename
    import os
    
    UPLOAD_FOLDER = os.path.join("static", "uploads", "groups", "icons")
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in {"png", "jpg", "jpeg", "webp", "gif"}:
        return jsonify({'success': False, 'message': 'Invalid image type. Use PNG/JPG/JPEG/WEBP/GIF.'})
    
    filename = secure_filename(f"group_{group_id}_icon.{ext}")
    save_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(save_path)
    
    icon_url = f"/static/uploads/groups/icons/{filename}"
    return jsonify({'success': True, 'url': icon_url})


@app.route('/group/<int:group_id>/add-moderator', methods=['POST'])
@login_required
def add_group_moderator(group_id):
    """Add or update a user as moderator/admin in a group"""
    user_id = session.get('user_id')
    is_admin = session.get('role') == 'admin'
    
    if not can_edit_group_settings(group_id, user_id, is_admin):
        return jsonify({'success': False, 'message': 'You do not have permission to manage moderators'})
    
    data = request.json
    target_user_id = data.get('user_id')
    role = data.get('role', 'moderator')
    
    if not target_user_id:
        return jsonify({'success': False, 'message': 'User ID required'})
    
    if role not in ['admin', 'moderator']:
        return jsonify({'success': False, 'message': 'Invalid role'})
    
    conn = get_conn()
    c = conn.cursor()
    
    # Check if user exists
    c.execute("SELECT username FROM users WHERE id = ?", (target_user_id,))
    user = c.fetchone()
    if not user:
        conn.close()
        return jsonify({'success': False, 'message': 'User not found'})
    
    # Check if already a member
    c.execute("SELECT id, role FROM group_members WHERE group_id = ? AND user_id = ?", (group_id, target_user_id))
    member = c.fetchone()
    
    if member:
        # Update existing role
        c.execute("UPDATE group_members SET role = ? WHERE group_id = ? AND user_id = ?", (role, group_id, target_user_id))
    else:
        # Add as new member with role
        c.execute("INSERT INTO group_members (group_id, user_id, role) VALUES (?, ?, ?)", (group_id, target_user_id, role))
        c.execute("UPDATE community_groups SET member_count = member_count + 1 WHERE id = ?", (group_id,))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': f'{user[0]} is now a {role}', 'username': user[0], 'role': role})


@app.route('/group/<int:group_id>/upload-banner', methods=['POST'])
@login_required
def upload_group_banner(group_id):
    """Upload community group banner"""
    user_id = session.get('user_id')
    is_admin = session.get('role') == 'admin'
    
    if not can_edit_group_settings(group_id, user_id, is_admin):
        return jsonify({'success': False, 'message': 'You do not have permission to edit this group'})
    
    file = request.files.get('file')
    if not file or not file.filename:
        return jsonify({'success': False, 'message': 'No file uploaded'})
    
    from werkzeug.utils import secure_filename
    import os
    
    UPLOAD_FOLDER = os.path.join("static", "uploads", "groups", "banners")
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in {"png", "jpg", "jpeg", "webp", "gif"}:
        return jsonify({'success': False, 'message': 'Invalid image type. Use PNG/JPG/JPEG/WEBP/GIF.'})
    
    filename = secure_filename(f"group_{group_id}_banner.{ext}")
    save_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(save_path)
    
    banner_url = f"/static/uploads/groups/banners/{filename}"
    return jsonify({'success': True, 'url': banner_url})


@app.route('/group/<int:group_id>/update', methods=['POST'])
@login_required
def update_group_settings(group_id):
    """Update community group settings"""
    user_id = session.get('user_id')
    is_admin = session.get('role') == 'admin'
    
    if not can_edit_group_settings(group_id, user_id, is_admin):
        return jsonify({'success': False, 'message': 'You do not have permission to edit this group'})
    
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    group_type = data.get('group_type')
    category = data.get('category')
    icon_url = data.get('icon_url')
    banner_url = data.get('banner_url')
    
    if not name:
        return jsonify({'success': False, 'message': 'Group name is required'})
    
    try:
        conn = get_conn()
        c = conn.cursor()
        
        c.execute("""
            UPDATE community_groups 
            SET name = ?, description = ?, group_type = ?, category = ?, icon_url = ?, banner_url = ?
            WHERE id = ?
        """, (name, description, group_type, category, icon_url, banner_url, group_id))
        
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Settings updated successfully'})
    except Exception as e:
        logger.error(f"Error updating group {group_id}: {e}")
        return jsonify({'success': False, 'message': str(e)})


@app.route('/group/<int:group_id>/post', methods=['POST'])
@login_required
def create_group_post(group_id):
    """Create a post in a group with optional attachments"""
    user_id = session.get('user_id')
    
    # Handle multipart form data if files are present, else JSON
    if request.is_json:
        data = request.get_json()
        title = data.get('title', '')
        content = data.get('content', '')
        post_type = data.get('post_type', 'discussion')
    else:
        title = request.form.get('title', '')
        content = request.form.get('content', '')
        post_type = request.form.get('post_type', 'discussion')
        channel_id = request.form.get('channel_id')
    
    if not content:
        return jsonify({'success': False, 'message': 'Content is required'})
    
    conn = get_conn()
    c = conn.cursor()
    
    try:
        # Insert post
        c.execute("""
            INSERT INTO group_posts (group_id, user_id, title, content, post_type, channel_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (group_id, user_id, title, content, post_type, channel_id))
        post_id = c.lastrowid
        
        # Handle attachments if any
        if 'attachments' in request.files:
            files = request.files.getlist('attachments')
            from werkzeug.utils import secure_filename
            import os
            
            UPLOAD_FOLDER = os.path.join("static", "uploads", "groups", "posts", str(post_id))
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            
            for file in files:
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    save_path = os.path.join(UPLOAD_FOLDER, filename)
                    file.save(save_path)
                    
                    file_url = f"/static/uploads/groups/posts/{post_id}/{filename}"
                    file_type = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'unknown'
                    
                    c.execute("""
                        INSERT INTO group_post_attachments (post_id, file_url, file_type, file_name)
                        VALUES (?, ?, ?, ?)
                    """, (post_id, file_url, file_type, filename))
        
        # Handle manga links from form data (JSON or form)
        manga_links = []
        external_attachments = []
        if request.is_json:
            manga_links = data.get('manga_links', [])
            external_attachments = data.get('external_attachments', [])
        else:
            m_links_raw = request.form.get('manga_links')
            if m_links_raw:
                import json
                try:
                    manga_links = json.loads(m_links_raw)
                except:
                    pass
            
            ext_raw = request.form.get('external_attachments')
            if ext_raw:
                import json
                try:
                    external_attachments = json.loads(ext_raw)
                except:
                    pass
        
        for m_id in manga_links:
            c.execute("""
                INSERT INTO group_post_attachments (post_id, file_url, file_type, file_name)
                VALUES (?, ?, ?, ?)
            """, (post_id, f"/manga/detail/{m_id}", "manga_link", f"Manga:{m_id}"))

        for item in external_attachments:
            url = item.get('url')
            f_type = item.get('type')
            if url and f_type:
                c.execute("""
                    INSERT INTO group_post_attachments (post_id, file_url, file_type, file_name)
                    VALUES (?, ?, ?, ?)
                """, (post_id, url, f_type, f"External {f_type.upper()}"))

        # Update post count
        c.execute("UPDATE community_groups SET post_count = post_count + 1 WHERE id = ?", (group_id,))
        
        conn.commit()
        return jsonify({'success': True, 'post_id': post_id})
    except Exception as e:
        logger.error(f"Error creating post: {e}")
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()


@app.route('/group/post/<int:post_id>/edit', methods=['POST'])
@login_required
def edit_group_post(post_id):
    """Edit a group post"""
    user_id = session.get('user_id')
    is_admin = session.get('role') == 'admin'
    
    conn = get_conn()
    c = conn.cursor()
    
    try:
        # Check ownership
        c.execute("SELECT user_id, group_id FROM group_posts WHERE id = ?", (post_id,))
        post = c.fetchone()
        
        if not post:
            return jsonify({'success': False, 'message': 'Post not found'})
        
        if post[0] != user_id and not is_admin:
            return jsonify({'success': False, 'message': 'You can only edit your own posts'})
        
        data = request.get_json()
        content = data.get('content', '').strip()
        
        if not content:
            return jsonify({'success': False, 'message': 'Content cannot be empty'})
        
        c.execute("UPDATE group_posts SET content = ? WHERE id = ?", (content, post_id))
        conn.commit()
        
        return jsonify({'success': True, 'message': 'Post updated successfully'})
    except Exception as e:
        logger.error(f"Error editing post: {e}")
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()


@app.route('/group/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_group_post(post_id):
    """Delete a group post"""
    user_id = session.get('user_id')
    is_admin = session.get('role') == 'admin'
    
    conn = get_conn()
    c = conn.cursor()
    
    try:
        # Check ownership
        c.execute("SELECT user_id, group_id FROM group_posts WHERE id = ?", (post_id,))
        post = c.fetchone()
        
        if not post:
            return jsonify({'success': False, 'message': 'Post not found'})
        
        if post[0] != user_id and not is_admin:
            return jsonify({'success': False, 'message': 'You can only delete your own posts'})
        
        group_id = post[1]
        
        # Delete votes first to avoid foreign key constraints
        c.execute("DELETE FROM group_post_votes WHERE post_id = ?", (post_id,))
        
        # Delete attachments
        c.execute("DELETE FROM group_post_attachments WHERE post_id = ?", (post_id,))
        
        # Delete comments and their attachments
        c.execute("SELECT id FROM group_comments WHERE post_id = ?", (post_id,))
        comment_ids = [row[0] for row in c.fetchall()]
        for cid in comment_ids:
            c.execute("DELETE FROM group_comment_attachments WHERE comment_id = ?", (cid,))
            c.execute("DELETE FROM group_comment_likes WHERE comment_id = ?", (cid,))
        c.execute("DELETE FROM group_comments WHERE post_id = ?", (post_id,))
        
        # Delete the post
        c.execute("DELETE FROM group_posts WHERE id = ?", (post_id,))
        
        # Update post count
        c.execute("UPDATE community_groups SET post_count = post_count - 1 WHERE id = ? AND post_count > 0", (group_id,))
        
        conn.commit()
        
        return jsonify({'success': True, 'message': 'Post deleted successfully'})
    except Exception as e:
        logger.error(f"Error deleting post: {e}")
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()


@app.route('/group/post/<int:post_id>/vote', methods=['POST'])
@login_required
def vote_group_post(post_id):
    """Vote on a group post (upvote or downvote)"""
    user_id = session.get('user_id')
    data = request.get_json()
    vote = data.get('vote', 0)  # 1 for upvote, -1 for downvote
    
    if vote not in [1, -1]:
        return jsonify({'success': False, 'message': 'Invalid vote'})
    
    conn = get_conn()
    c = conn.cursor()
    
    try:
        # Check current vote
        c.execute("SELECT vote FROM group_post_votes WHERE post_id = ? AND user_id = ?", (post_id, user_id))
        existing = c.fetchone()
        
        if existing:
            if existing[0] == vote:
                # Same vote = remove vote
                c.execute("DELETE FROM group_post_votes WHERE post_id = ? AND user_id = ?", (post_id, user_id))
                if vote == 1:
                    c.execute("UPDATE group_posts SET upvotes = upvotes - 1 WHERE id = ?", (post_id,))
                else:
                    c.execute("UPDATE group_posts SET downvotes = downvotes - 1 WHERE id = ?", (post_id,))
                new_vote = 0
            else:
                # Different vote = change vote
                c.execute("UPDATE group_post_votes SET vote = ? WHERE post_id = ? AND user_id = ?", (vote, post_id, user_id))
                if vote == 1:
                    c.execute("UPDATE group_posts SET upvotes = upvotes + 1, downvotes = downvotes - 1 WHERE id = ?", (post_id,))
                else:
                    c.execute("UPDATE group_posts SET upvotes = upvotes - 1, downvotes = downvotes + 1 WHERE id = ?", (post_id,))
                new_vote = vote
        else:
            # New vote
            c.execute("INSERT INTO group_post_votes (post_id, user_id, vote) VALUES (?, ?, ?)", (post_id, user_id, vote))
            if vote == 1:
                c.execute("UPDATE group_posts SET upvotes = upvotes + 1 WHERE id = ?", (post_id,))
            else:
                c.execute("UPDATE group_posts SET downvotes = downvotes + 1 WHERE id = ?", (post_id,))
            new_vote = vote
        
        # Get new counts
        c.execute("SELECT upvotes, downvotes FROM group_posts WHERE id = ?", (post_id,))
        counts = c.fetchone()
        
        conn.commit()
        
        return jsonify({
            'success': True, 
            'new_vote': new_vote,
            'upvotes': counts[0],
            'downvotes': counts[1],
            'score': counts[0] - counts[1]
        })
    except Exception as e:
        logger.error(f"Error voting on post: {e}")
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()


@app.route('/group/<int:group_id>/channels', methods=['GET'])
@login_required
def get_group_channels(group_id):
    """Get channels for a group"""
    conn = get_conn()
    c = conn.cursor()
    
    c.execute("""
        SELECT id, name, description, channel_type, icon, position
        FROM group_channels
        WHERE group_id = ?
        ORDER BY position ASC
    """, (group_id,))
    
    channels = [dict(zip(['id', 'name', 'description', 'type', 'icon', 'position'], row)) for row in c.fetchall()]
    conn.close()
    
    return jsonify({'success': True, 'channels': channels})


@app.route('/group/<int:group_id>/channels', methods=['POST'])
@login_required
def create_group_channel(group_id):
    """Create a new channel in a group"""
    user_id = session.get('user_id')
    is_admin = session.get('role') == 'admin'
    
    # Check if user can manage channels (admin or group owner)
    if not can_edit_group_settings(group_id, user_id, is_admin):
        return jsonify({'success': False, 'message': 'Not authorized'})
    
    data = request.get_json()
    name = data.get('name', '').strip().lower().replace(' ', '-')
    description = data.get('description', '')
    channel_type = data.get('type', 'text')
    
    if not name:
        return jsonify({'success': False, 'message': 'Channel name required'})
    
    conn = get_conn()
    c = conn.cursor()
    
    try:
        # Get next position
        c.execute("SELECT MAX(position) FROM group_channels WHERE group_id = ?", (group_id,))
        max_pos = c.fetchone()[0] or 0
        
        c.execute("""
            INSERT INTO group_channels (group_id, name, description, channel_type, icon, position)
            VALUES (?, ?, ?, ?, 'hash', ?)
        """, (group_id, name, description, channel_type, max_pos + 1))
        
        channel_id = c.lastrowid
        conn.commit()
        
        return jsonify({'success': True, 'channel_id': channel_id, 'name': name})
    except Exception as e:
        logger.error(f"Error creating channel: {e}")
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()


@app.route('/group/post/<int:post_id>/comments', methods=['GET'])
@login_required
def get_group_post_comments(post_id):
    """Fetch comments for a post"""
    user_id = session.get('user_id')
    sort_by = request.args.get('sort', 'oldest')
    
    conn = get_conn()
    c = conn.cursor()
    
    # Determine order clause
    order_clause = "gc.created_at ASC"
    if sort_by == 'newest':
        order_clause = "gc.created_at DESC"
    elif sort_by == 'most_reacted':
        order_clause = "reaction_count DESC, gc.created_at DESC"

    query = f"""
        SELECT gc.id, gc.content, gc.created_at, u.username, u.avatar_url, u.id as user_id,
               (SELECT reaction_type FROM group_comment_likes WHERE comment_id = gc.id AND user_id = ?) as user_reaction,
               (SELECT COUNT(*) FROM group_comment_likes WHERE comment_id = gc.id) as reaction_count
        FROM group_comments gc
        JOIN users u ON gc.user_id = u.id
        WHERE gc.post_id = ?
        ORDER BY {order_clause}
    """
    
    c.execute(query, (user_id, post_id))
    
    rows = c.fetchall()
    comments = []
    for r in rows:
        comment_id = r[0]
        
        # Get reaction counts grouped by type
        c.execute("SELECT reaction_type, COUNT(*) FROM group_comment_likes WHERE comment_id = ? GROUP BY reaction_type", (comment_id,))
        reactions = {}
        total_reactions = 0
        for rx_type, rx_count in c.fetchall():
            reactions[rx_type] = rx_count
            total_reactions += rx_count

        # Get attachments for this comment
        c.execute("SELECT file_url, file_type, file_name, manga_id, manga_title, manga_cover FROM group_comment_attachments WHERE comment_id = ?", (comment_id,))
        attachments = []
        for row in c.fetchall():
            att = {'url': row[0], 'type': row[1], 'name': row[2]}
            if row[3]:  # manga_id
                att['manga_id'] = row[3]
            if row[4]:  # manga_title
                att['manga_title'] = row[4]
            if row[5]:  # manga_cover
                att['manga_cover'] = row[5]
            attachments.append(att)
        
        # Apply mentions filter to comment content
        comment_content = str(r[1])
        try:
            from app import mentions_filter
            comment_content = mentions_filter(comment_content)
        except:
            pass

        comments.append({
            'id': r[0],
            'content': comment_content,
            'created_at': r[2],
            'username': r[3],
            'avatar': r[4],
            'user_id': r[5],
            'user_reaction': r[6],
            'reactions': reactions,
            'total_reactions': total_reactions,
            'attachments': attachments
        })
    
    conn.close()
    return jsonify(comments)


@app.route('/group/comment/<int:comment_id>/vote', methods=['POST'])
@login_required
def vote_group_comment(comment_id):
    """React to a comment"""
    user_id = session.get('user_id')
    data = request.get_json()
    reaction_type = data.get('reaction_type', 'like')
    
    conn = get_conn()
    c = conn.cursor()
    
    try:
        # Check existing reaction
        c.execute("SELECT reaction_type FROM group_comment_likes WHERE comment_id = ? AND user_id = ?", (comment_id, user_id))
        existing = c.fetchone()
        
        current_action = 'added'
        
        if existing:
            if existing[0] == reaction_type:
                # Toggle off
                c.execute("DELETE FROM group_comment_likes WHERE comment_id = ? AND user_id = ?", (comment_id, user_id))
                current_action = 'removed'
            else:
                # Change reaction
                c.execute("UPDATE group_comment_likes SET reaction_type = ? WHERE comment_id = ? AND user_id = ?", (reaction_type, comment_id, user_id))
                current_action = 'updated'
        else:
            # Add new reaction
            c.execute("INSERT INTO group_comment_likes (comment_id, user_id, reaction_type) VALUES (?, ?, ?)", (comment_id, user_id, reaction_type))
            
            # Notification logic (simplified)
            c.execute("SELECT user_id FROM group_comments WHERE id = ?", (comment_id,))
            author = c.fetchone()
            if author and author[0] != user_id:
                msg = f"reacted with {reaction_type} to your comment"
                c.execute("INSERT INTO notifications (user_id, message, type, link) VALUES (?, ?, 'reaction', ?)", 
                          (author[0], msg, f"/community")) # Ideally link to specific post

        conn.commit()
        
        # Return updated counts
        c.execute("SELECT reaction_type, COUNT(*) FROM group_comment_likes WHERE comment_id = ? GROUP BY reaction_type", (comment_id,))
        reactions = {}
        total = 0
        for rx, count in c.fetchall():
            reactions[rx] = count
            total += count
            
        return jsonify({
            'success': True,
            'action': current_action,
            'user_reaction': reaction_type if current_action != 'removed' else None,
            'reactions': reactions,
            'total_reactions': total
        })
        
    except Exception as e:
        logger.error(f"Error reacting to comment: {e}")
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()


@app.route('/group/comment/<int:comment_id>/delete', methods=['DELETE'])
@login_required
def delete_group_comment(comment_id):
    """Delete a comment"""
    user_id = session.get('user_id')
    role = session.get('role')
    
    conn = get_conn()
    c = conn.cursor()
    
    try:
        # Check ownership or admin
        c.execute("SELECT user_id, post_id FROM group_comments WHERE id = ?", (comment_id,))
        row = c.fetchone()
        if not row:
            return jsonify({'success': False, 'message': 'Comment not found'})
            
        owner_id, post_id = row
        if owner_id != user_id and role != 'admin':
             return jsonify({'success': False, 'message': 'Permission denied'})
             
        c.execute("DELETE FROM group_comments WHERE id = ?", (comment_id,))
        # Decrement comment count
        c.execute("UPDATE group_posts SET comment_count = comment_count - 1 WHERE id = ? AND comment_count > 0", (post_id,))
        
        conn.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error deleting comment: {e}")
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()


@app.route('/group/comment/<int:comment_id>/edit', methods=['POST'])
@login_required
def edit_group_comment(comment_id):
    """Edit a comment"""
    user_id = session.get('user_id')
    data = request.get_json()
    new_content = data.get('content')
    
    if not new_content:
        return jsonify({'success': False, 'message': 'Content required'})
        
    conn = get_conn()
    c = conn.cursor()
    
    try:
        # Check ownership
        c.execute("SELECT user_id FROM group_comments WHERE id = ?", (comment_id,))
        row = c.fetchone()
        if not row:
            return jsonify({'success': False, 'message': 'Comment not found'})
            
        if row[0] != user_id:
             return jsonify({'success': False, 'message': 'Permission denied'})
             
        c.execute("UPDATE group_comments SET content = ? WHERE id = ?", (new_content, comment_id))
        conn.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error editing comment: {e}")
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()


@app.route('/group/comment/<int:comment_id>/like', methods=['POST'])
@login_required
def like_group_comment(comment_id):
    """Toggle like on a group comment"""
    user_id = session.get('user_id')
    conn = get_conn()
    c = conn.cursor()
    
    try:
        c.execute("SELECT 1 FROM group_comment_likes WHERE comment_id = ? AND user_id = ?", (comment_id, user_id))
        liked = c.fetchone()
        
        if liked:
            c.execute("DELETE FROM group_comment_likes WHERE comment_id = ? AND user_id = ?", (comment_id, user_id))
            status = 'unliked'
        else:
            c.execute("INSERT INTO group_comment_likes (comment_id, user_id) VALUES (?, ?)", (comment_id, user_id))
            status = 'liked'
            
        conn.commit()
        
        # Get new count
        c.execute("SELECT COUNT(*) FROM group_comment_likes WHERE comment_id = ?", (comment_id,))
        count = c.fetchone()[0]
        
        return jsonify({'success': True, 'status': status, 'like_count': count})
    except Exception as e:
        logger.error(f"Error liking comment: {e}")
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()




@app.route('/group/post/<int:post_id>/comment', methods=['POST'])
@login_required
def post_group_comment(post_id):
    """Post a comment on a post"""
    user_id = session.get('user_id')
    
    has_attachments = False
    if 'attachments' in request.files and request.files.getlist('attachments'):
        # Check if actual files are selected (sometimes empty field is sent)
        files = request.files.getlist('attachments')
        if any(f.filename for f in files):
            has_attachments = True
            
    has_external = False
    if request.is_json:
        data = request.get_json()
        content = data.get('content', '')
        if data.get('external_attachments'):
            has_external = True
    else:
        content = request.form.get('content', '')
        ext_raw = request.form.get('external_attachments')
        if ext_raw:
            try:
                import json
                exts = json.loads(ext_raw)
                if exts:
                    has_external = True
            except:
                pass
    
    if not content and not has_attachments and not has_external:
        return jsonify({'success': False, 'message': 'Comment cannot be empty'})
    
    conn = get_conn()
    c = conn.cursor()
    
    try:
        # Insert comment
        c.execute("""
            INSERT INTO group_comments (post_id, user_id, content)
            VALUES (?, ?, ?)
        """, (post_id, user_id, content))
        comment_id = c.lastrowid
        
        # Handle attachments
        if 'attachments' in request.files:
            files = request.files.getlist('attachments')
            from werkzeug.utils import secure_filename
            import os
            
            UPLOAD_FOLDER = os.path.join("static", "uploads", "groups", "comments", str(comment_id))
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            
            for file in files:
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    save_path = os.path.join(UPLOAD_FOLDER, filename)
                    file.save(save_path)
                    
                    file_url = f"/static/uploads/groups/comments/{comment_id}/{filename}"
                    file_type = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'unknown'
                    
                    c.execute("""
                        INSERT INTO group_comment_attachments (comment_id, file_url, file_type, file_name)
                        VALUES (?, ?, ?, ?)
                    """, (comment_id, file_url, file_type, filename))
        
        # Handle external attachments
        external_attachments = []
        if request.is_json:
            external_attachments = data.get('external_attachments', [])
        else:
            ext_raw = request.form.get('external_attachments')
            if ext_raw:
                import json
                try:
                    external_attachments = json.loads(ext_raw)
                except:
                    pass
        
        for item in external_attachments:
            url = item.get('url')
            f_type = item.get('type')
            if url and f_type:
                manga_id = item.get('manga_id')
                manga_title = item.get('manga_title')
                manga_cover = item.get('manga_cover')
                c.execute("""
                    INSERT INTO group_comment_attachments (comment_id, file_url, file_type, file_name, manga_id, manga_title, manga_cover)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (comment_id, url, f_type, f"External {f_type.upper()}", manga_id, manga_title, manga_cover))

        # Update comment count on post
        c.execute("UPDATE group_posts SET comment_count = comment_count + 1 WHERE id = ?", (post_id,))
        
        conn.commit()
        return jsonify({'success': True, 'comment_id': comment_id})
    except Exception as e:
        logger.error(f"Error posting comment: {e}")
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()


@app.route('/group/<int:group_id>/poll', methods=['POST'])
@login_required
def create_group_poll(group_id):
    """Create a poll post in a group"""
    user_id = session.get('user_id')
    data = request.get_json()
    
    question = data.get('question')
    options = data.get('options', [])
    allow_multiple = data.get('allow_multiple', False)
    expires_in = data.get('expires_in', 7)  # default 7 days
    channel_id = data.get('channel_id')  # Get the selected channel
    
    if not question or not options or len(options) < 2:
        return jsonify({'success': False, 'message': 'Question and at least 2 options are required'})
    
    conn = get_conn()
    c = conn.cursor()
    
    try:
        # Create the post first
        c.execute("""
            INSERT INTO group_posts (group_id, user_id, title, content, post_type, channel_id)
            VALUES (?, ?, ?, ?, 'poll', ?)
        """, (group_id, user_id, question, question, channel_id))
        post_id = c.lastrowid
        
        # Calculate expiry
        expires_at = (datetime.utcnow() + timedelta(days=int(expires_in))).isoformat()
        
        # Create the poll
        c.execute("""
            INSERT INTO group_polls (post_id, question, allow_multiple, expires_at)
            VALUES (?, ?, ?, ?)
        """, (post_id, question, 1 if allow_multiple else 0, expires_at))
        poll_id = c.lastrowid
        
        # Create the options
        for opt_text in options:
            if opt_text.strip():
                c.execute("INSERT INTO group_poll_options (poll_id, option_text) VALUES (?, ?)", (poll_id, opt_text.strip()))
        
        # Update post count
        c.execute("UPDATE community_groups SET post_count = post_count + 1 WHERE id = ?", (group_id,))
        
        conn.commit()
        return jsonify({'success': True, 'post_id': post_id})
    except Exception as e:
        logger.error(f"Error creating poll: {e}")
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()


@app.route('/group/poll/<int:poll_id>/vote', methods=['POST'])
@login_required
def vote_group_poll(poll_id):
    """Vote on a poll"""
    user_id = session.get('user_id')
    data = request.get_json()
    option_ids = data.get('option_ids', [])
    
    if not option_ids:
        return jsonify({'success': False, 'message': 'No options selected'})
    
    conn = get_conn()
    c = conn.cursor()
    
    try:
        # Check if poll exists
        c.execute("SELECT allow_multiple, expires_at FROM group_polls WHERE id = ?", (poll_id,))
        poll = c.fetchone()
        if not poll:
            return jsonify({'success': False, 'message': 'Poll not found'})
        
        # Check expiry
        from datetime import datetime
        if poll[1] and datetime.fromisoformat(poll[1]) < datetime.utcnow():
            return jsonify({'success': False, 'message': 'Poll has expired'})
        
        allow_multiple = poll[0]
        if not allow_multiple and len(option_ids) > 1:
            return jsonify({'success': False, 'message': 'Multiple choices not allowed'})
        
        # Remove existing votes for this user in this poll
        c.execute("DELETE FROM group_poll_votes WHERE poll_id = ? AND user_id = ?", (poll_id, user_id))
        
        # Add new votes
        for opt_id in option_ids:
            c.execute("INSERT INTO group_poll_votes (poll_id, option_id, user_id) VALUES (?, ?, ?)", (poll_id, opt_id, user_id))
        
        # Get new results
        c.execute("""
            SELECT id, option_text, (SELECT COUNT(*) FROM group_poll_votes WHERE option_id = gpo.id) as votes
            FROM group_poll_options gpo
            WHERE poll_id = ?
        """, (poll_id,))
        options = [dict(zip(['id', 'text', 'votes'], row)) for row in c.fetchall()]
        
        conn.commit()
        return jsonify({'success': True, 'options': options})
    except Exception as e:
        logger.error(f"Error voting on poll: {e}")
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()



@app.route('/discover')
@login_required
def discover_groups():
    """Discovery page for community groups"""
    sort_by = request.args.get('sort', 'all')
    
    conn = get_conn()
    c = conn.cursor()
    
    # Build query based on sort parameter
    try:
        # Base query - get all columns
        base_query = "SELECT * FROM community_groups"
        
        # Add ORDER BY based on sort parameter
        if sort_by == 'members':
            base_query += " ORDER BY COALESCE(member_count, 0) DESC"
        elif sort_by == 'popular':
            base_query += " ORDER BY COALESCE(member_count, 0) DESC, COALESCE(post_count, 0) DESC"
        elif sort_by == 'active':
            base_query += " ORDER BY COALESCE(post_count, 0) DESC"
        elif sort_by == 'new':
            base_query += " ORDER BY created_at DESC"
        elif sort_by == 'trending':
            # Trending = combination of recent activity and growth
            base_query += " ORDER BY COALESCE(post_count, 0) DESC, COALESCE(member_count, 0) DESC"
        # 'all' = no specific order
        
        c.execute(base_query)
        columns = [description[0] for description in c.description]
        all_rows = c.fetchall()
        groups = []
        for row in all_rows:
            g = dict(zip(columns, row))
            # Add default fields if missing
            if 'member_count' not in g or g['member_count'] is None:
                g['member_count'] = 120
            if 'icon_url' not in g:
                g['icon_url'] = None
            if 'post_count' not in g or g['post_count'] is None:
                g['post_count'] = 0
            groups.append(g)
    except Exception as e:
        logger.error(f"Error fetching groups: {e}")
        groups = []
    finally:
        conn.close()
    
    # Organize by type
    import random
    featured_groups = groups[:4] 
    if len(groups) > 4 and sort_by == 'all':
        featured_groups = random.sample(groups, 4)
    elif len(groups) > 4:
        featured_groups = groups[:4]  # Top 4 based on sort
        
    genre_groups = [g for g in groups if g.get('group_type') == 'genre']
    manga_groups = [g for g in groups if g.get('group_type') == 'manga']
    
    return render_template('discover_groups.html', 
                          featured_groups=featured_groups,
                          genre_groups=genre_groups, 
                          manga_groups=manga_groups,
                          current_sort=sort_by)


@app.route('/api/community/posts', methods=['POST'])
@login_required
def api_create_community_post():
    """API endpoint to create a new community post"""
    try:
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        post_type = request.form.get('post_type', 'discussion')
        group_id = request.form.get('group_id', '')
        manga_id = request.form.get('manga_id', None)
        gif_url = request.form.get('gif_url', None)
        poll_options = request.form.getlist('poll_options[]')
        
        user_id = session.get('user_id')
        
        if not title or not content:
            return jsonify({'error': 'Title and content are required'}), 400
        
        conn = get_conn()
        c = conn.cursor()

        # If no group_id is selected, default to 'World' group
        if not group_id:
            c.execute("SELECT id FROM community_groups WHERE name = 'World' AND group_type = 'system' LIMIT 1")
            world_group = c.fetchone()
            if world_group:
                group_id = world_group[0]
            else:
                # Fallback in case World group doesn't exist for some reason
                return jsonify({'error': 'Please select a group to post to or ensure World group exists'}), 400
        
        # Try to find a default channel if group_id is known
        channel_id = request.form.get('channel_id')
        if not channel_id and group_id:
            c.execute("SELECT id FROM group_channels WHERE group_id = ? ORDER BY position ASC LIMIT 1", (group_id,))
            chan_row = c.fetchone()
            if chan_row:
                channel_id = chan_row[0]

        # Insert post into group_posts
        c.execute("""
            INSERT INTO group_posts (user_id, group_id, title, content, post_type, manga_id, gif_url, channel_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, DATETIME('now'))
        """, (user_id, group_id, title, content, post_type, manga_id, gif_url, channel_id))
        
        post_id = c.lastrowid

        # Insert poll data if it's a poll (Standardized Schema)
        if post_type == 'poll' and poll_options:
            c.execute("""
                INSERT INTO group_polls (post_id, question)
                VALUES (?, ?)
            """, (post_id, title))
            poll_id = c.lastrowid
            
            for option in poll_options:
                if option.strip():
                    c.execute("""
                        INSERT INTO group_poll_options (poll_id, option_text)
                        VALUES (?, ?)
                    """, (poll_id, option.strip()))
        
        # Handle file attachments
        if 'attachments' in request.files:
            files = request.files.getlist('attachments')
            import os
            from werkzeug.utils import secure_filename
            import time
            
            for file in files:
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    upload_dir = os.path.join('static', 'uploads', 'groups', 'posts', str(post_id))
                    os.makedirs(upload_dir, exist_ok=True)
                    
                    unique_name = f"{int(time.time())}_{filename}"
                    file_path = os.path.join(upload_dir, unique_name)
                    file.save(file_path)
                    
                    file_url = '/' + file_path.replace('\\', '/')
                    file_type = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'image'
                    
                    c.execute("""
                        INSERT INTO group_post_attachments (post_id, file_url, file_type, file_name)
                        VALUES (?, ?, ?, ?)
                    """, (post_id, file_url, file_type, filename))
        
        # Also handle manga link as an attachment if provided
        if manga_id and post_type == 'recommendation':
            file_url = f"/manga/detail/{manga_id}"
            c.execute("""
                INSERT INTO group_post_attachments (post_id, file_url, file_type, file_name)
                VALUES (?, ?, ?, ?)
            """, (post_id, file_url, 'manga_link', 'Linked Manga'))

        # Update group post count
        c.execute("UPDATE community_groups SET post_count = post_count + 1 WHERE id = ?", (group_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'post_id': post_id}), 201
        
    except Exception as e:
        if 'conn' in locals():
            conn.close()
        logger.error(f"Error creating post: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == "__main__":

    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)



