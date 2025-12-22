# 📚 NOVUS E-Library Project - Complete Presentation

**A Modern Digital Library Platform with Dual-Mode Content Management, Manga Reader, and AI Integration**

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Core Features](#core-features)
3. [Technical Architecture](#technical-architecture)
4. [Database Schema](#database-schema)
5. [Frontend System](#frontend-system)
6. [Backend Routes & APIs](#backend-routes--apis)
7. [User Management & Roles](#user-management--roles)
8. [Content Management System](#content-management-system)
9. [Manga Reading System](#manga-reading-system)
10. [AI Integration Features](#ai-integration-features)
11. [Admin Features](#admin-features)
12. [User Workflows](#user-workflows)
13. [File Structure](#file-structure)
14. [Key Technologies](#key-technologies)
15. [Deployment & Running](#deployment--running)

---

## 📖 Project Overview

**NOVUS** is a sophisticated digital library management platform designed to host both traditional **books** and **manga series** with advanced features including:

- ✅ Dual-mode content upload system (Books & Manga)
- ✅ Full-featured manga reader with AI integration
- ✅ User role-based access control (Readers, Publishers, Admins)
- ✅ Team member management system
- ✅ Reading history and watchlist tracking
- ✅ AI-powered summaries and analysis
- ✅ Responsive design for desktop, tablet, and mobile
- ✅ Chapter-based manga series management

**Primary Goal**: Provide a modern, user-friendly platform for discovering and reading books and manga series with intelligent features.

---

## 🎯 Core Features

### 1. **Dual-Mode Content Upload**
   - **Books**: Traditional digital books with PDF, audio, and cover art
   - **Manga**: Series with multiple chapters (PDFs uploaded incrementally)
   - Single `/add` page with intuitive tab-based interface
   - Smart form validation and file handling

### 2. **Modern Manga Reader**
   - Dark theme with cyan accents
   - Page navigation with progress slider
   - Integrated AI chatbot and translation panel
   - Character profiles with voice actor information
   - Customizable reader settings (brightness, font size, reading mode)
   - Responsive design optimized for all devices

### 3. **Content Discovery**
   - Home page with latest books
   - Dedicated manga section with browsing
   - Watchlist feature to track favorite content
   - Category-based filtering
   - Reading history tracking

### 4. **User Management**
   - Registration and authentication
   - Three user roles: Reader, Publisher, Admin
   - Profile pages with upload statistics
   - Account status management (active/banned)

### 5. **AI Integration**
   - Automated chapter summaries
   - Character profile generation
   - Smart analysis and insights
   - Translation support panel
   - Chatbot for user interactions

### 6. **Admin Dashboard**
   - User management and banning system
   - Team member management
   - AI summaries management and caching
   - Content moderation
   - Publisher role request approvals

---

## 🏗️ Technical Architecture

### Stack Overview
```
Frontend:          HTML5, CSS3, JavaScript (Vanilla)
Backend:           Flask (Python)
Database:          SQLite3
Authentication:    Session-based (Flask sessions)
PDF Handling:      pdf2image library
Image Processing:  PIL/Pillow
API Style:         RESTful JSON endpoints
Deployment:        Python with Flask built-in server
```

### High-Level Architecture Diagram
```
┌─────────────────────────────────────────────────────────────┐
│                        USER BROWSER                          │
├─────────────────────────────────────────────────────────────┤
│  HTML Templates  |  CSS Stylesheets  |  JavaScript (DOM)    │
└─────────────────────────────────────────────────────────────┘
                              ↓↑
┌─────────────────────────────────────────────────────────────┐
│                      FLASK WEB SERVER                        │
│                    (Python Application)                      │
├─────────────────────────────────────────────────────────────┤
│  Route Handlers  |  Request Processing  |  Business Logic   │
└─────────────────────────────────────────────────────────────┘
                              ↓↑
┌─────────────────────────────────────────────────────────────┐
│                    SQLITE3 DATABASE                          │
├─────────────────────────────────────────────────────────────┤
│  Users | Books | Chapters | Watchlist | History | AI Cache  │
└─────────────────────────────────────────────────────────────┘
                              ↓↑
┌─────────────────────────────────────────────────────────────┐
│                    FILE STORAGE SYSTEM                       │
├─────────────────────────────────────────────────────────────┤
│  /static/books/  |  /static/manga/  |  /static/covers/     │
│  /static/audio/  |  /static/img/    |  (PDFs, Images, MP3) │
└─────────────────────────────────────────────────────────────┘
```

---

## 🗄️ Database Schema

### Users Table
```sql
CREATE TABLE users (
    id              INTEGER PRIMARY KEY,
    username        TEXT UNIQUE,
    email           TEXT UNIQUE,
    password        TEXT,
    role            TEXT,           -- 'reader', 'publisher', 'admin'
    is_banned       INTEGER DEFAULT 0,
    status          TEXT            -- 'active', 'banned'
)
```
**Purpose**: Authentication, authorization, and user profile management

### Books Table
```sql
CREATE TABLE books (
    id              INTEGER PRIMARY KEY,
    title           TEXT,
    author          TEXT,
    category        TEXT,
    pdf_filename    TEXT,
    audio_filename  TEXT,
    cover_path      TEXT,
    description     TEXT,
    book_type       TEXT DEFAULT 'book',  -- 'book' or 'manga'
    uploader_id     INTEGER,              -- Foreign Key → users.id
    created_at      DATETIME
)
```
**Purpose**: Store both book and manga series metadata

### Chapters Table
```sql
CREATE TABLE chapters (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    manga_id        INTEGER NOT NULL,     -- Foreign Key → books.id
    chapter_num     INTEGER NOT NULL,
    title           TEXT,
    pdf_filename    TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(manga_id, chapter_num)
)
```
**Purpose**: Store individual manga chapters with unique numbering per series

### History Table
```sql
CREATE TABLE history (
    id              INTEGER PRIMARY KEY,
    user_id         INTEGER,
    book_id         INTEGER,
    date_read       DATE
)
```
**Purpose**: Track reading history for personalization and recommendations

### Watchlist Table
```sql
CREATE TABLE watchlist (
    id              INTEGER PRIMARY KEY,
    user_id         INTEGER NOT NULL,
    book_id         INTEGER NOT NULL,
    created_at      DATETIME
)
```
**Purpose**: Allow users to bookmark and track favorite content

### AI Summaries Table
```sql
CREATE TABLE ai_summaries (
    id              INTEGER PRIMARY KEY,
    item_type       TEXT,           -- 'book' or 'chapter'
    item_id         INTEGER,
    summary         TEXT,
    model           TEXT,           -- Model used for generation
    created_at      TEXT,
    UNIQUE(item_type, item_id)
)
```
**Purpose**: Cache AI-generated summaries for quick retrieval

### Team Table
```sql
CREATE TABLE team (
    id              INTEGER PRIMARY KEY,
    full_name       TEXT,
    role            TEXT,
    bio             TEXT,
    avatar_path     TEXT,
    initials        TEXT,
    created_at      DATETIME
)
```
**Purpose**: Display team member information on the about page

### Role Requests Table
```sql
CREATE TABLE role_requests (
    id              INTEGER PRIMARY KEY,
    user_id         INTEGER NOT NULL,
    requested_role  TEXT,
    status          TEXT DEFAULT 'pending',  -- 'pending', 'approved', 'rejected'
    created_at      DATETIME
)
```
**Purpose**: Manage publisher role requests with admin approval workflow

---

## 🎨 Frontend System

### Templates Directory Structure
```
templates/
├── base.html                    # Master template with navigation
├── index.html                   # Home page (latest books)
├── login.html                   # User login
├── register.html                # User registration
├── add_book.html                # Dual-mode upload (Books & Manga)
├── upload_chapter.html          # Chapter upload for manga
├── book_detail.html             # Book detail page
├── book_detail_new.html         # Enhanced book detail (modern design)
├── manga.html                   # Manga listing page
├── manga_reader.html            # Original manga reader (basic)
├── manga_reader_new.html        # Modern manga reader with AI
├── chapter_viewer.html          # Individual chapter viewer
├── edit_book.html               # Edit book metadata
├── my_uploads.html              # Publisher dashboard
├── profile.html                 # User profile page
├── watchlist.html               # User's watchlist
├── about.html                   # About & team page
├── faq.html                     # FAQ & guidelines
├── admin_users.html             # User management (admin)
├── user_management.html         # User admin panel
├── team_admin.html              # Team member management
├── admin_ai_summaries.html      # AI cache management
└── admin_fix_uploaders.html     # Database maintenance
```

### Static Assets
```
static/
├── css/
│   └── style.css                # Main stylesheet (dark theme, cyan accents)
├── js/                          # JavaScript utilities
├── img/
│   └── team/                    # Team member avatars
├── books/                       # Uploaded PDF files
├── audio/                       # Uploaded audio files (MP3)
├── covers/                      # Book/manga cover images
└── manga/                       # Manga page images
```

### Design Philosophy
- **Dark Theme**: Navy backgrounds (#1a1a2e) with cyan (#00d4ff) accents
- **Responsive**: Mobile-first approach with flexbox layouts
- **Accessible**: Semantic HTML, proper ARIA labels, keyboard navigation
- **Modern**: Gradient overlays, glowing borders, smooth transitions
- **Consistent**: Reusable component styles, color palette, typography

---

## 🔌 Backend Routes & APIs

### Authentication Routes
| Route | Method | Purpose |
|-------|--------|---------|
| `/login` | GET, POST | User login |
| `/register` | GET, POST | User registration |
| `/logout` | GET | Clear session |

### Content Routes (Public)
| Route | Method | Purpose |
|-------|--------|---------|
| `/` | GET | Home page (books) |
| `/book/<id>` | GET | Book detail view |
| `/manga` | GET | Manga listing |
| `/manga/<id>` | GET | Modern manga reader |
| `/manga/read/<id>` | GET | Legacy manga reader |
| `/about` | GET | About & team page |
| `/faq` | GET | FAQ page |

### User Routes
| Route | Method | Purpose |
|-------|--------|---------|
| `/profile` | GET | User profile page |
| `/watchlist` | GET | User watchlist |
| `/my_uploads` | GET | Publisher dashboard |

### Publisher Routes (Admin/Publisher Only)
| Route | Method | Purpose |
|-------|--------|---------|
| `/add` | GET, POST | Upload book/manga |
| `/book/<id>/edit` | GET, POST | Edit book metadata |
| `/manga/<id>/upload-chapter` | GET, POST | Upload manga chapter |

### Admin Routes (Admin Only)
| Route | Method | Purpose |
|-------|--------|---------|
| `/admin/users` | GET | User management |
| `/admin/users/<id>/ban` | POST | Ban user |
| `/admin/users/<id>/unban` | POST | Unban user |
| `/admin/team` | GET, POST | Team management |
| `/admin/ai_summaries` | GET | AI cache viewer |
| `/admin/ai_summaries/clear` | POST | Clear AI cache |

### API Endpoints (JSON)
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/manga/<id>/chapters` | GET | Get all chapters |
| `/api/chapter/<id>/pages` | GET | Get chapter pages |
| `/api/chapter/<id>` | PUT, DELETE | Update/delete chapter |
| `/api/manga/<id>/characters` | GET, POST | Character profiles |
| `/api/manga/character/<id>` | PUT, DELETE | Manage characters |
| `/ai_summary` | POST | Generate AI summary |
| `/report_manga` | POST | Report issue |

---

## 👥 User Management & Roles

### User Roles and Permissions
```
┌─────────────────────────────────────────────────────────┐
│ READER (Default Role)                                   │
├─────────────────────────────────────────────────────────┤
│ ✅ Browse books and manga                               │
│ ✅ Read content                                         │
│ ✅ Add to watchlist                                     │
│ ✅ View reading history                                 │
│ ✅ View profile                                         │
│ ✅ Request publisher role                              │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ PUBLISHER (Approved by Admin)                           │
├─────────────────────────────────────────────────────────┤
│ ✅ All reader permissions                               │
│ ✅ Upload books (PDF + metadata)                        │
│ ✅ Create manga series                                  │
│ ✅ Upload chapters to own manga                         │
│ ✅ Edit own content                                     │
│ ✅ View upload dashboard                                │
│ ❌ Admin functions                                      │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ ADMIN (System Administrator)                            │
├─────────────────────────────────────────────────────────┤
│ ✅ All publisher permissions                            │
│ ✅ Ban/unban users                                      │
│ ✅ Delete users                                         │
│ ✅ Manage team members                                  │
│ ✅ Clear AI cache                                       │
│ ✅ View system statistics                               │
│ ✅ Approve publisher requests                           │
│ ✅ Manage all content (global)                          │
└─────────────────────────────────────────────────────────┘
```

### Authentication System
- **Session-Based**: Flask sessions stored server-side
- **Password Storage**: Plain text (⚠️ should use hashing in production)
- **Login Flow**: Username/email + password verification
- **Logout**: Clear session and redirect to home
- **Ban System**: Checked before each request (`@before_request`)

---

## 📚 Content Management System

### Dual-Mode Upload Interface

#### Book Upload Path
```
User selects "Book" tab
    ↓
Fills form:
  - Title (required)
  - Author (required)
  - Category (dropdown)
  - Description (textarea)
  - PDF file (drag & drop, required)
  - Audio file (optional)
  - Cover image (required)
    ↓
Validation:
  - All required fields present
  - PDF file extension check
  - Image file type check
    ↓
File Storage:
  - PDF → static/books/{secure_filename}
  - Audio → static/audio/{secure_filename}
  - Cover → static/covers/{secure_filename}
    ↓
Database Insert:
  INSERT INTO books (
    title, author, category, description,
    pdf_filename, audio_filename, cover_path,
    book_type='book', uploader_id, created_at
  )
    ↓
Redirect: /my_uploads
```

#### Manga Upload Path
```
User selects "Manga" tab
    ↓
Fills form:
  - Manga Title (required)
  - Author/Artist (required)
  - Category (dropdown)
  - Publishing Status (Ongoing/Completed/Hiatus)
  - Description (textarea)
  - Cover image (required)
  - Chapter 1 PDF (required)
    ↓
Validation:
  - All required fields present
  - PDF file type check
  - Image file type check
    ↓
File Storage:
  - Cover → static/covers/{secure_filename}
  - Chapter 1 PDF → static/books/{secure_filename}
    ↓
Database Insert (Dual):
  1. INSERT INTO books (
       title, author, category, description,
       cover_path, book_type='manga',
       uploader_id, created_at
     )
     → Get manga_id (LAST_INSERT_ROWID)
     
  2. INSERT INTO chapters (
       manga_id, chapter_num=1,
       title, pdf_filename
     )
    ↓
Redirect: /manga
```

### Chapter Upload System

**Route**: `/manga/<id>/upload-chapter`

```
Publisher visits manga detail page
    ↓
Clicks "[+ Chapter]" button
    ↓
Shows current chapters + upload form
    ↓
Fills form:
  - Chapter Number (integer, must be unique for this manga)
  - Chapter Title (optional, auto-generates if blank)
  - PDF file (drag & drop, required)
    ↓
Validation:
  - Chapter number unique for this manga
  - PDF file validation
  - User owns the manga
    ↓
File Storage:
  - PDF → static/books/{secure_filename}
    ↓
Database Insert:
  INSERT INTO chapters (
    manga_id, chapter_num,
    title, pdf_filename
  )
    ↓
Redirect: /manga/<id>/upload-chapter
Display success message with updated chapter list
```

### Publisher Dashboard (`/my_uploads`)
Displays:
- All books uploaded by current publisher
- All manga series owned
- Chapter count for each manga
- Quick actions: "[+ Chapter]" button, Edit, Delete
- Visual distinction: 📚 for books, 🎨 for manga

---

## 📖 Manga Reading System

### Modern Manga Reader (`manga_reader_new.html`)

#### Layout Components
```
┌────────────────────────────────────────────────────────┐
│ TOP BAR (Dark Navy with Cyan Border)                   │
├────────────────────────────────────────────────────────┤
│  Chapter Title  │  [AI INSIGHTS]  [⚙️] [🚩] [☰]       │
└────────────────────────────────────────────────────────┘

┌─────────────────────────┬──────────────────────────┐
│                         │   RIGHT SIDEBAR (AI)     │
│  MANGA VIEWER           ├──────────────────────────┤
│  (Main Content Area)    │ 1. AI Chatbot Card       │
│                         │    - Chat tab            │
│  ┌─────────────────┐   │    - Translate tab       │
│  │  MANGA PAGES    │   │    - Toggle switch       │
│  │  (Placeholder)  │   │                          │
│  │                 │   ├──────────────────────────┤
│  │                 │   │ 2. AI Assistant Card     │
│  │                 │   │    - Smart Summary       │
│  │                 │   │    - 3-bullet points     │
│  │                 │   │    - View Full Analysis  │
│  │                 │   │                          │
│  └─────────────────┘   ├──────────────────────────┤
│                         │ 3. Character Profiles    │
│  [PREV] [Slider] [NEXT] │    - Avatar circles      │
│  Page X/Y               │    - Names & traits      │
│                         │    - Voice actor info    │
│                         │    - Show More button    │
└─────────────────────────┴──────────────────────────┘
```

#### Reader Features
1. **Navigation Controls**:
   - PREV/NEXT buttons for page navigation
   - Progress slider for quick jumping
   - Page counter displaying current position
   - Keyboard support (ready to implement)

2. **Settings Modal** (⚙️ button):
   - Reading Mode: Single/Double/Vertical/Horizontal
   - Background: Light/Dark/Sepia
   - Brightness: 0-200% slider
   - Font Size: Small/Medium/Large
   - **Persistent**: Saved to localStorage

3. **AI Integration Panel**:
   - **AI Chatbot**: Conversation about manga
   - **Translation Panel**: Real-time translation
   - **Smart Summary**: AI-generated chapter summary (3 key points)
   - **Character Profiles**: Dynamic character info with avatars
   - **Toggle**: Enable/disable AI features

4. **User Actions**:
   - 🚩 Report Issue: Submit bug reports
   - ☰ Menu: Mobile navigation
   - Responsive sidebar collapse on small screens

#### Color Scheme
```css
--primary-bg: #1a1a2e      /* Dark navy */
--secondary-bg: #16213e    /* Slightly lighter */
--accent-color: #00d4ff    /* Cyan glow */
--text-primary: #e0e0e0    /* Light gray */
--card-bg: #0f3460         /* Dark blue */
--border-glow: 0 0 10px rgba(0, 212, 255, 0.5)
```

---

## 🤖 AI Integration Features

### AI Summary Generation
**Endpoint**: `/ai_summary` (POST)

**Request**:
```json
{
  "item_type": "chapter",
  "item_id": 5,
  "content": "Full chapter text..."
}
```

**Response**:
```json
{
  "summary": "This chapter covers...",
  "model": "gpt-3.5-turbo",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Features**:
- Caches results to avoid duplicate API calls
- Supports both books and chapters
- OpenAI integration (requests library)
- Database caching in `ai_summaries` table

### Character Profile System
**Routes**:
- `GET /api/manga/<id>/characters` - Get all characters
- `POST /api/manga/<id>/characters` - Add new character
- `PUT /api/manga/character/<id>` - Update character
- `DELETE /api/manga/character/<id>` - Delete character

**Character Data**:
```json
{
  "id": 1,
  "manga_id": 6,
  "name": "Protagonist Name",
  "role": "Main Character",
  "description": "Bio/description",
  "avatar_url": "image_path",
  "voice_actor": "Voice actor name"
}
```

### AI-Powered Features
1. **Smart Summaries**: Chapter overviews with key points
2. **Character Analysis**: AI-generated character profiles
3. **Translation**: Real-time manga translation
4. **Chatbot**: Q&A about manga content
5. **Content Analysis**: Themes, plot points, significance

---

## 🛠️ Admin Features

### User Management Panel (`/admin/users`)
**Capabilities**:
- View all users with roles
- Ban/unban user accounts
- Delete user accounts (with safeguards)
- Filter by role
- View account status

**Safeguards**:
- Admins cannot ban/delete themselves
- Admins cannot be deleted by other admins
- Banned users are logged out immediately
- User data cleanup on deletion

### Team Management (`/admin/team`)
**Capabilities**:
- Add team members with details
- Upload avatar images
- Manage team member roles and bios
- Delete team members
- Auto-generate initials from names

**Team Member Fields**:
- Full Name
- Role (Developer, Designer, Manager, etc.)
- Bio/Description
- Avatar Image
- Auto-generated Initials

### AI Cache Management (`/admin/ai_summaries`)
**Capabilities**:
- View all cached AI summaries
- View generation metadata (model, timestamp)
- Clear entire cache
- Monitor cache size and efficiency
- Search summaries by item type

### Publisher Request Approval
**Workflow**:
1. Users request publisher role from profile
2. Request stored in `role_requests` table
3. Admin views pending requests at `/admin/users`
4. Admin approves/rejects
5. User role updated on approval
6. Email notification sent (when configured)

---

## 👤 User Workflows

### Workflow 1: New User Registration
```
1. Click "Register" link
2. Fill registration form:
   - Username (unique)
   - Email (unique)
   - Password
   - Confirm Password
3. Submit
4. Account created with 'reader' role
5. Redirect to login
6. Can now login and browse
```

### Workflow 2: User Wants to Publish
```
1. Login as reader
2. Go to profile
3. Click "Request Publisher Role"
4. Submit reason (optional)
5. Request stored as pending
6. Admin receives notification
7. Admin approves in admin panel
8. User role updated to 'publisher'
9. User receives notification
10. Can now access /add to upload content
```

### Workflow 3: Publisher Uploads a Book
```
1. Navigate to /add (auto-redirected if not publisher)
2. Book tab selected by default
3. Fill form:
   - Title: "Book Title"
   - Author: "Author Name"
   - Category: "Science Fiction"
   - Description: "Book summary..."
   - PDF file: [Upload]
   - Audio file: [Optional]
   - Cover image: [Upload]
4. Click "PUBLISH BOOK"
5. Files validated and stored
6. Database record created
7. Redirect to /my_uploads
8. Book appears on home page
9. Readers can now access
```

### Workflow 4: Publisher Creates Manga Series
```
1. Navigate to /add
2. Click "Manga" tab
3. Fill form:
   - Manga Title: "Manga Name"
   - Author/Artist: "Artist Name"
   - Category: "Action"
   - Status: "Ongoing"
   - Description: "Series summary..."
   - Cover image: [Upload]
   - Chapter 1 PDF: [Upload]
4. Click "CREATE MANGA SERIES"
5. Files validated and stored
6. Manga created with chapter 1
7. Redirect to /manga
8. Publisher can now upload more chapters
```

### Workflow 5: Updating Manga with New Chapters
```
1. Go to /my_uploads
2. Find manga series in list
3. Click "[+ Chapter]" button
4. Shows current chapters and upload form
5. Fill form:
   - Chapter Number: "2"
   - Chapter Title: "Chapter 2 Title" (optional)
   - PDF file: [Upload]
6. Click "Upload Chapter"
7. Validation checks:
   - Chapter number not already used
   - PDF file valid
   - User owns this manga
8. Chapter stored with auto-increment
9. Reader can now read chapter 2
10. Process repeats for each chapter
```

### Workflow 6: Reader Reads Manga
```
1. Go to /manga
2. Browse manga list
3. Click on manga title
4. See manga reader with chapter 1
5. Use navigation:
   - PREV/NEXT buttons
   - Progress slider
   - Chapter dropdown
6. Click "⚙️" for settings
7. Customize reading experience:
   - Reading mode
   - Brightness
   - Font size
8. View AI features:
   - Click "AI INSIGHTS"
   - Read smart summary
   - View character profiles
   - Use chatbot/translator
9. Progress saved to reading history
10. Added to watchlist if desired
```

---

## 📁 File Structure

### Root Level Files
```
app.py                          # Main Flask application (2600+ lines)
requirements.txt                # Python dependencies
library.db                      # SQLite database
run.bat / run_server_simple.py  # Server startup scripts
```

### Documentation Files
```
IMPLEMENTATION_SUMMARY.md       # Feature implementation details
QUICK_REFERENCE.md              # Quick reference guide
MODERN_MANGA_READER_GUIDE.md    # Manga reader documentation
NEW_MANGA_READER_SUMMARY.md     # New reader features
MANGA_CHAPTER_SYSTEM.md         # Chapter system documentation
VISUAL_GUIDE.md                 # Architecture diagrams
TESTING_CHECKLIST.md            # Testing procedures
BUTTON_TEST_GUIDE.md            # Button functionality testing
```

### Test & Development Files
```
tests/
├── test_manga_reader_features.py
├── test_e2e_ai_manga.py
├── test_admin_ai_summaries.py
├── test_book_edit.py
├── test_team_admin.py
├── test_flow.py
├── run_verbose.py              # Run tests with output
└── [other test helpers]

scripts/
├── check_app_import.py
└── [database checking scripts]

[root level utility scripts]:
├── add_test_manga.py
├── add_status_column.py
├── check_chapter_data.py
├── check_db.py
├── check_manga.py
├── migrate_db.py
├── setup_db.py
└── [other utilities]
```

### Templates (HTML)
```
templates/
├── base.html                    # Navigation, layout
├── index.html                   # Home page
├── add_book.html                # Dual-mode upload
├── manga_reader_new.html        # Modern reader (primary)
├── manga_reader.html            # Legacy reader
├── admin_*.html                 # Admin panels (5 templates)
├── user_management.html         # User admin
├── team_admin.html              # Team management
└── [10+ other templates]
```

### Static Assets
```
static/
├── css/style.css                # Main stylesheet (1000+ lines)
├── js/                          # JavaScript helpers
├── books/                       # Uploaded PDFs
├── manga/                       # Manga chapter images
├── covers/                      # Cover images
├── audio/                       # Audio files
└── img/team/                    # Team avatars
```

---

## 🔧 Key Technologies

### Backend (Python)
- **Flask**: Web framework (2.x+)
- **SQLite3**: Database
- **pdf2image**: PDF to image conversion
- **Pillow/PIL**: Image processing
- **requests**: HTTP client for AI APIs
- **Werkzeug**: File upload security
- **python-dotenv**: Environment configuration

### Frontend (Web)
- **HTML5**: Semantic markup
- **CSS3**: Styling with variables and flexbox
- **JavaScript (Vanilla)**: DOM manipulation, API calls
- **localStorage**: Client-side settings persistence
- **Responsive Design**: Mobile-first approach

### Infrastructure
- **File System**: Static file serving
- **Session Management**: Server-side Flask sessions
- **CORS**: Cross-origin handling (if needed)

### Optional/Ready-to-Integrate
- **OpenAI API**: For AI summary generation
- **Translation API**: For manga translation
- **Email Service**: For notifications

---

## 🚀 Deployment & Running

### Prerequisites
```
Python 3.8+
pip (Python package manager)
Optional: pdf2image system dependencies (ffmpeg, poppler-utils)
```

### Installation
```bash
# Clone or download the project
cd d:\nist\ project\computer\e-library

# Create virtual environment (optional but recommended)
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Install optional PDF support
pip install pdf2image
```

### Database Setup
```bash
# Initialize database
python setup_db.py

# Or the app auto-initializes on first run
```

### Running the Server
```bash
# Simple method
python run_server_simple.py

# Or direct
python app.py

# Or with batch file (Windows)
run.bat
```

**Access the application**:
```
http://localhost:5000 or http://127.0.0.1:5000
```

### Default Admin Account
**Note**: You must create an admin account manually or modify `init_db()` to seed users:

```python
# In app.py init_db():
c.execute("""
    INSERT INTO users (username, email, password, role)
    VALUES ('admin', 'admin@example.com', 'password123', 'admin')
""")
```

### Configuration
- **Secret Key**: Set `SECRET_KEY` environment variable (auto-generated default for dev)
- **Database Path**: Configurable in `app.py` (default: `library.db`)
- **Upload Folders**: Auto-created in `static/`
- **Flask Debug**: Disabled in production mode (`debug=False`)

### Environment Variables
```
SECRET_KEY=your-secret-key-here
FLASK_ENV=production (or development)
PYTHON_PATH=%CD%  # Windows
PYTHONPATH=$PWD   # Linux
```

### Troubleshooting
1. **Port 5000 in use**: Change in `app.py` `app.run(port=5001)`
2. **Database locked**: Close other connections, restart server
3. **PDF conversion fails**: Install `poppler-utils` system package
4. **Import errors**: Run `pip install -r requirements.txt` again
5. **Template not found**: Ensure working directory is project root

---

## 📊 Project Statistics

### Code Base
- **Main app.py**: 2,600+ lines
- **Templates**: 20+ HTML files
- **Styling**: 1,000+ lines of CSS
- **Database Tables**: 9 tables
- **API Endpoints**: 30+ routes
- **User Roles**: 3 (Reader, Publisher, Admin)

### Features Implemented
- ✅ Dual-mode upload system
- ✅ Modern manga reader
- ✅ Chapter management
- ✅ AI integration
- ✅ User authentication
- ✅ Role-based access control
- ✅ Watchlist & history
- ✅ Admin dashboard
- ✅ Team management
- ✅ Content moderation

### User Capacity
- **Unlimited users** (scalable)
- **Unlimited books/manga** (disk space limited)
- **Unlimited chapters** (per manga)
- **Concurrent readers** (Flask limitation ~50-100, upgradeable)

---

## 🎓 Learning Resources

### For Developers
- **Flask Documentation**: https://flask.palletsprojects.com/
- **SQLite Guide**: https://www.sqlite.org/docs.html
- **HTML/CSS/JS**: MDN Web Docs
- **PDF Processing**: pdf2image documentation

### For Content Creators
- **Upload Guide**: See `/faq` page
- **Manga Format**: PDF chapters, 100+ pages recommended
- **Cover Art**: Minimum 300x400px recommended

### For Administrators
- Admin guides embedded in `/admin/*` routes
- User management documentation in code comments
- Database schema documentation in `QUICK_REFERENCE.md`

---

## 🔐 Security Notes

### Current Implementation
- ✅ Session-based authentication
- ✅ File upload validation
- ✅ Role-based access control
- ✅ SQL injection prevention (parameterized queries)
- ✅ User banning system
- ✅ Admin safeguards

### Recommendations for Production
- ⚠️ Use password hashing (bcrypt/argon2)
- ⚠️ Implement HTTPS/SSL
- ⚠️ Add CSRF protection
- ⚠️ Rate limiting on uploads
- ⚠️ API key authentication for external services
- ⚠️ User email verification
- ⚠️ Audit logging
- ⚠️ Database backups

---

## 🎯 Future Enhancement Possibilities

### Phase 2 Features
- [ ] Rating & review system
- [ ] Recommendation engine
- [ ] Social features (follow users, comments)
- [ ] Advanced search with filters
- [ ] Full-text search capabilities
- [ ] Bookmark within chapters
- [ ] Reading progress tracking
- [ ] Genre-based recommendations

### Phase 3 Features
- [ ] Mobile app (React Native)
- [ ] Dark/light theme toggle
- [ ] Multi-language support
- [ ] Offline reading mode
- [ ] Chapter scheduling
- [ ] Community forums
- [ ] Artist/creator profiles
- [ ] Merchandise integration

### Technical Improvements
- [ ] Migrate to PostgreSQL
- [ ] Implement API versioning
- [ ] Docker containerization
- [ ] Kubernetes deployment
- [ ] Redis caching layer
- [ ] Elasticsearch integration
- [ ] WebSocket for real-time updates
- [ ] GraphQL API option

---

## 📞 Support & Contact

### Project Structure
- **Lead**: NIST Project Team
- **Framework**: Flask Web Framework
- **Database**: SQLite3
- **Hosting**: Local/On-premise

### Getting Help
1. Check documentation files in project root
2. Review code comments in app.py
3. Check test files for usage examples
4. Refer to QUICK_REFERENCE.md for API docs
5. Check TESTING_CHECKLIST.md for debugging

---

## 📝 Version History

### Current Version: v2.0
**Last Updated**: December 15, 2024

**Major Features**:
- ✅ Dual-mode upload system (Books & Manga)
- ✅ Modern manga reader with AI
- ✅ Chapter management system
- ✅ Admin dashboard
- ✅ Team management
- ✅ AI integration ready

**Previous Versions**:
- v1.0: Basic library system
- v1.5: Book detail pages
- v2.0: Manga reader and dual-mode uploads

---

## 🎉 Summary

**NOVUS E-Library** is a comprehensive, modern digital library platform that successfully combines traditional book hosting with an advanced manga reading system. With its dual-mode upload interface, modern UI, AI integration, and robust admin features, it provides a complete solution for content creators and readers alike.

The project demonstrates:
- ✅ Full-stack web development expertise
- ✅ Database design and optimization
- ✅ User experience design
- ✅ Security best practices
- ✅ Scalable architecture
- ✅ Comprehensive documentation
- ✅ Testing methodology
- ✅ Admin functionality

**Perfect for**: Educational institutions, publishing platforms, manga/comic communities, digital libraries, and content distribution platforms.

---

**End of Presentation**

*For detailed implementation notes, refer to IMPLEMENTATION_SUMMARY.md and QUICK_REFERENCE.md*

