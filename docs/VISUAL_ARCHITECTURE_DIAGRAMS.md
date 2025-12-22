# NOVUS E-Library - Visual Architecture & Workflow Diagrams

## 1. System Architecture Overview

```
╔════════════════════════════════════════════════════════════════════════════╗
║                          NOVUS E-LIBRARY SYSTEM                            ║
╚════════════════════════════════════════════════════════════════════════════╝

┌──────────────────────────────────────────────────────────────────────────┐
│                            CLIENT LAYER                                   │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │ Browser Environment (HTML5, CSS3, JavaScript)                     │  │
│  │  ├─ Responsive UI (Desktop, Tablet, Mobile)                       │  │
│  │  ├─ localStorage for settings persistence                         │  │
│  │  ├─ AJAX/Fetch API for dynamic content                          │  │
│  │  └─ Event listeners for user interactions                        │  │
│  └────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
                                    ↓ HTTP/JSON
┌──────────────────────────────────────────────────────────────────────────┐
│                         FLASK WEB SERVER                                   │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │ Route Handler Layer                                               │  │
│  │  ├─ Authentication (@before_request)                             │  │
│  │  ├─ Route decorators (@admin_required, @role_required)           │  │
│  │  ├─ Session management                                           │  │
│  │  └─ Request/Response processing                                  │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │ Business Logic Layer                                              │  │
│  │  ├─ File upload handling (PDF, Images, Audio)                    │  │
│  │  ├─ PDF to image conversion (pdf2image)                          │  │
│  │  ├─ File validation & security                                   │  │
│  │  ├─ AI integration (OpenAI API calls)                            │  │
│  │  ├─ Role-based authorization                                     │  │
│  │  └─ Content management logic                                      │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │ Template Rendering Layer                                          │  │
│  │  ├─ Jinja2 template engine                                        │  │
│  │  ├─ Dynamic content injection                                     │  │
│  │  ├─ User role-based template variants                            │  │
│  │  └─ Form rendering & validation                                  │  │
│  └────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
                                    ↓ SQL Queries
┌──────────────────────────────────────────────────────────────────────────┐
│                          DATA ACCESS LAYER                                │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │ SQLite3 Database Manager (library.db)                            │  │
│  │  ├─ Connection pooling                                            │  │
│  │  ├─ Transaction management                                        │  │
│  │  ├─ Parameterized queries (SQL injection prevention)             │  │
│  │  ├─ Trigger management (created_at defaults)                     │  │
│  │  └─ Data integrity constraints                                    │  │
│  └────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
                                    ↓ File I/O
┌──────────────────────────────────────────────────────────────────────────┐
│                       FILE STORAGE LAYER                                  │
│  ┌─────────────────┬─────────────────┬──────────────────┬──────────────┐ │
│  │  static/books/  │  static/manga/  │  static/covers/  │ static/audio/│ │
│  │  PDFs           │  Chapter images │  Cover artwork   │  MP3 files   │ │
│  └─────────────────┴─────────────────┴──────────────────┴──────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘

```

---

## 2. User Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         NEW USER JOURNEY                                 │
└─────────────────────────────────────────────────────────────────────────┘

START → http://localhost:5000/
         ↓
    ┌─ HOME PAGE ─┐
    │ (Index)     │
    │ Books list  │
    └─────────────┘
         ↓
    ┌──────────────────────────────────────────────┐
    │  Visitor choices:                            │
    │  [Browse Books] [Go to Manga] [Sign Up] [Login] │
    └──────────────────────────────────────────────┘
         ↓
    ┌─────────────────────────────────────────────────────────────┐
    │                                                              │
    ├─→ [Browse Books] → /book/<id> → Book detail page          │
    │                    ↓                                        │
    │                    Can view PDF, audio, details            │
    │                    (no account needed)                      │
    │                                                              │
    ├─→ [Go to Manga] → /manga → List all manga                │
    │                    ↓                                        │
    │                    /manga/<id> → Modern reader             │
    │                    Can read with AI features               │
    │                                                              │
    ├─→ [Sign Up] → /register → CREATE NEW ACCOUNT              │
    │                 ↓                                           │
    │                 Fill: Username, Email, Password            │
    │                 ↓                                           │
    │                 INSERT INTO users (role='reader')          │
    │                 ↓                                           │
    │                 Redirect to /login                         │
    │                 ↓                                           │
    │ [Login] → /login → AUTHENTICATE                            │
    │            ↓                                               │
    │            Verify password                                 │
    │            ↓                                               │
    │            session['user_id'] = user_id                    │
    │            ↓                                               │
    │            Redirect to /                                   │
    │                                                              │
    └─────────────────────────────────────────────────────────────┘
         ↓
    ┌─ AUTHENTICATED USER ─────────────────────────────────┐
    │  (session_id set, user_id in session)                │
    │                                                        │
    │  Available routes:                                    │
    │  • /profile        - User profile & stats            │
    │  • /watchlist      - Saved bookmarks                 │
    │  • /my_uploads     - Only if publisher/admin         │
    │  • /add            - Only if publisher/admin         │
    │  • /admin/*        - Only if admin                   │
    │  • /logout         - Clear session                   │
    │                                                        │
    └────────────────────────────────────────────────────────┘
         ↓
    ┌──────────────────────────────────────────────────────┐
    │         READER ROLE WORKFLOWS                        │
    ├──────────────────────────────────────────────────────┤
    │ [View Profile] → /profile → See reading history     │
    │                  ↓                                    │
    │                  Stats: Books read, Manga chapters   │
    │                  ↓                                    │
    │                  [Request Publisher Role]            │
    │                  ↓                                    │
    │                  INSERT INTO role_requests           │
    │                  ↓                                    │
    │                  Admin notification                  │
    │                  ↓ (Admin approves)                  │
    │                  UPDATE users SET role='publisher'   │
    │                  ↓                                    │
    │                  User now has upload access          │
    │                                                       │
    │ [Add to Watchlist] → (on book/manga page)           │
    │                      INSERT INTO watchlist           │
    │                      ↓                               │
    │                      /watchlist shows all items      │
    │                                                       │
    └──────────────────────────────────────────────────────┘
         ↓
    ┌──────────────────────────────────────────────────────┐
    │       PUBLISHER ROLE WORKFLOWS                       │
    ├──────────────────────────────────────────────────────┤
    │ [Upload Content] → /add (dual-tab interface)        │
    │                    ↓                                  │
    │        ┌────────────┴────────────┐                   │
    │        │                         │                   │
    │   [BOOK TAB]              [MANGA TAB]               │
    │   - Title                 - Title                    │
    │   - Author                - Artist                   │
    │   - Category              - Category                 │
    │   - Description           - Status                   │
    │   - PDF file              - Cover                    │
    │   - Audio (opt)           - Chapter 1 PDF            │
    │   - Cover                                            │
    │        │                         │                   │
    │        └────────────┬────────────┘                   │
    │                     ↓                                 │
    │        INSERT INTO books (book_type)                │
    │        ↓                                             │
    │        If manga: INSERT INTO chapters (#1)          │
    │        ↓                                             │
    │        /my_uploads shows all uploads                │
    │                                                       │
    │ [Add Chapter] → /manga/<id>/upload-chapter         │
    │                 ↓                                    │
    │                 Show existing chapters              │
    │                 ↓                                    │
    │                 Upload form:                        │
    │                 - Chapter number (unique)           │
    │                 - Chapter title (opt)               │
    │                 - PDF file                          │
    │                 ↓                                    │
    │                 Validate & store                    │
    │                 INSERT INTO chapters                │
    │                 ↓                                    │
    │                 Readers can now access              │
    │                                                       │
    │ [Edit Content] → /book/<id>/edit                    │
    │                  ↓                                   │
    │                  Metadata only (PDF can't change)   │
    │                  ↓                                   │
    │                  UPDATE books SET ...               │
    │                                                       │
    │ [View Dashboard] → /my_uploads                      │
    │                    ↓                                 │
    │                    All owned books/manga            │
    │                    Quick actions for each           │
    │                    Chapter counts                   │
    │                                                       │
    └──────────────────────────────────────────────────────┘
         ↓
    ┌──────────────────────────────────────────────────────┐
    │          ADMIN ROLE WORKFLOWS                        │
    ├──────────────────────────────────────────────────────┤
    │ [User Management] → /admin/users                    │
    │                     ↓                                │
    │                     See all users                    │
    │                     [Ban User] → UPDATE status='ban'│
    │                     [Delete User] → DELETE FROM      │
    │                     [Approve Publisher] → UPDATE     │
    │                                                       │
    │ [Team Admin] → /admin/team                         │
    │                 ↓                                    │
    │                 Add team members                    │
    │                 Upload avatars                      │
    │                 Manage bios & roles                │
    │                                                       │
    │ [AI Cache] → /admin/ai_summaries                   │
    │               ↓                                      │
    │               View cached summaries                 │
    │               [Clear Cache] → DELETE all            │
    │                                                       │
    │ All publisher permissions +                         │
    │ Admin-only features                                 │
    │                                                       │
    └──────────────────────────────────────────────────────┘
         ↓
    LOGOUT → /logout → session.clear() → Redirect to /

```

---

## 3. Data Flow for Book Upload

```
PUBLISHER INITIATES UPLOAD
↓
GET /add
↓
Renders add_book.html with form
↓
┌─────────────────────────────────────────────────────────┐
│              BOOK UPLOAD FORM SUBMISSION                │
│                    POST /add                            │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Form Data:                                            │
│  ├─ title = "The Great Novel"                         │
│  ├─ author = "John Smith"                             │
│  ├─ category = "Fiction"                              │
│  ├─ description = "An amazing story..."               │
│  ├─ pdf_file = <PDF BINARY DATA>                      │
│  ├─ audio_file = <MP3 BINARY DATA>                    │
│  ├─ cover_file = <PNG BINARY DATA>                    │
│  └─ book_type = "book"                                │
│                                                         │
└─────────────────────────────────────────────────────────┘
│
├─ Validation Phase
│  ├─ Check user is authenticated ✓
│  ├─ Check user role is publisher/admin ✓
│  ├─ Validate all required fields present ✓
│  ├─ Check file extensions allowed ✓
│  ├─ Verify file sizes within limits ✓
│  └─ Confirm no SQL injection attempts ✓
│
├─ File Processing Phase
│  │
│  ├─ PDF File:
│  │  ├─ secure_filename("mybook.pdf")
│  │  ├─ Generate unique name: "pdf_1702656000_123.pdf"
│  │  ├─ Save to: static/books/pdf_1702656000_123.pdf
│  │  └─ pdf_filename = "pdf_1702656000_123.pdf"
│  │
│  ├─ Audio File (Optional):
│  │  ├─ secure_filename("mybook.mp3")
│  │  ├─ Generate unique name: "aud_1702656000_456.mp3"
│  │  ├─ Save to: static/audio/aud_1702656000_456.mp3
│  │  └─ audio_filename = "aud_1702656000_456.mp3"
│  │
│  └─ Cover Image:
│     ├─ secure_filename("cover.png")
│     ├─ Generate unique name: "cov_1702656000_789.png"
│     ├─ Save to: static/covers/cov_1702656000_789.png
│     └─ cover_path = "covers/cov_1702656000_789.png"
│
├─ Database Insert Phase
│  │
│  └─ SQL Query:
│     INSERT INTO books (
│       title,
│       author,
│       category,
│       description,
│       pdf_filename,
│       audio_filename,
│       cover_path,
│       book_type,
│       uploader_id,
│       created_at
│     ) VALUES (
│       'The Great Novel',
│       'John Smith',
│       'Fiction',
│       'An amazing story...',
│       'pdf_1702656000_123.pdf',
│       'aud_1702656000_456.mp3',
│       'covers/cov_1702656000_789.png',
│       'book',
│       42,  ← user_id from session
│       DATETIME('now')
│     )
│
│     Result: id = 101 (assigned by SQLite AUTOINCREMENT)
│
├─ Flash Message
│  └─ "Book published successfully!"
│
├─ Redirect
│  └─ HTTP 302 → /my_uploads
│
└─ Display Result
   │
   └─ User sees book in /my_uploads dashboard:
      ├─ Title: "The Great Novel"
      ├─ Author: "John Smith"
      ├─ Cover image displayed
      ├─ Action buttons: [Edit] [Delete] [+ Chapter]
      └─ Available to all readers on home page

```

---

## 4. Data Flow for Manga Upload

```
PUBLISHER INITIATES MANGA CREATION
↓
GET /add
↓
Renders add_book.html with form
↓
User clicks "Manga" tab
↓
┌─────────────────────────────────────────────────────────┐
│             MANGA UPLOAD FORM SUBMISSION                │
│                    POST /add                            │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Form Data:                                            │
│  ├─ title = "Dragon Hero"                            │
│  ├─ author = "Manga Artist"                           │
│  ├─ category = "Action"                               │
│  ├─ status = "Ongoing"                                │
│  ├─ description = "Epic action series..."             │
│  ├─ cover_file = <PNG BINARY DATA>                    │
│  ├─ chapter_1_pdf = <PDF BINARY DATA>                 │
│  └─ book_type = "manga"                               │
│                                                         │
└─────────────────────────────────────────────────────────┘
│
├─ Validation Phase
│  ├─ Check user is authenticated ✓
│  ├─ Check user role is publisher/admin ✓
│  ├─ Validate all required fields present ✓
│  ├─ Check file extensions allowed ✓
│  ├─ Verify file sizes within limits ✓
│  └─ Confirm no SQL injection attempts ✓
│
├─ File Processing Phase
│  │
│  ├─ Cover Image:
│  │  ├─ secure_filename("cover.png")
│  │  ├─ Generate unique name: "cov_1702656100_123.png"
│  │  ├─ Save to: static/covers/cov_1702656100_123.png
│  │  └─ cover_path = "covers/cov_1702656100_123.png"
│  │
│  └─ Chapter 1 PDF:
│     ├─ secure_filename("ch01.pdf")
│     ├─ Generate unique name: "pdf_1702656100_456.pdf"
│     ├─ Save to: static/books/pdf_1702656100_456.pdf
│     └─ ch1_pdf_filename = "pdf_1702656100_456.pdf"
│
├─ Database Insert Phase (PART 1: Create Manga Series)
│  │
│  └─ SQL Query (INSERT INTO books):
│     INSERT INTO books (
│       title,
│       author,
│       category,
│       description,
│       cover_path,
│       book_type,
│       uploader_id,
│       created_at
│     ) VALUES (
│       'Dragon Hero',
│       'Manga Artist',
│       'Action',
│       'Epic action series...',
│       'covers/cov_1702656100_123.png',
│       'manga',  ← Different from book!
│       42,  ← user_id from session
│       DATETIME('now')
│     )
│
│     Result: id = 150 (manga_id for future chapters)
│
├─ Database Insert Phase (PART 2: Create Chapter 1)
│  │
│  └─ SQL Query (INSERT INTO chapters):
│     INSERT INTO chapters (
│       manga_id,
│       chapter_num,
│       title,
│       pdf_filename,
│       created_at
│     ) VALUES (
│       150,  ← Just created manga series id
│       1,    ← Chapter 1
│       '',   ← Empty (will use default "Chapter 1")
│       'pdf_1702656100_456.pdf',
│       DATETIME('now')
│     )
│
│     Result: chapter id = 501
│
├─ Flash Message
│  └─ "Manga series created successfully!"
│
├─ Redirect
│  └─ HTTP 302 → /manga
│
└─ Display Result
   │
   └─ User sees manga in /manga listing:
      ├─ Title: "Dragon Hero"
      ├─ Author: "Manga Artist"
      ├─ Cover image displayed
      ├─ Status: "Ongoing"
      ├─ Chapter count: "1 chapter"
      ├─ Action buttons: [Read] [Edit] [+ Chapter]
      └─ Readers can now access and read Chapter 1

```

---

## 5. Chapter Upload Workflow

```
PUBLISHER ADDS NEW CHAPTER
↓
Navigates to /my_uploads
↓
Clicks "[+ Chapter]" button on manga series
↓
GET /manga/<id>/upload-chapter (manga_id = 150)
↓
┌──────────────────────────────────────────────────────────┐
│          CHAPTER UPLOAD PAGE RENDERED                    │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Existing Chapters Display:                             │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Chapter 1: "Chapter 1"     (Original upload)    │   │
│  │ Chapter 2: "The Beginning" (Added later)        │   │
│  │ Chapter 3: "Rising Tension"(Added later)        │   │
│  └─────────────────────────────────────────────────┘   │
│                                                          │
│  Upload Form:                                           │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Chapter Number: [4           ] ← Next auto       │   │
│  │ Chapter Title:  [New Chapter   ]  (optional)     │   │
│  │ PDF File:      [Choose File...] (required)     │   │
│  │ [Upload Chapter] button                         │   │
│  └─────────────────────────────────────────────────┘   │
│                                                          │
└──────────────────────────────────────────────────────────┘
│
User fills form:
├─ Chapter Number: 4
├─ Chapter Title: "The Turning Point"
└─ PDF File: chapter4.pdf
│
│
POST /manga/150/upload-chapter
↓
├─ Validation Phase
│  │
│  ├─ Check user owns this manga ✓
│  │  └─ SELECT uploader_id FROM books WHERE id=150
│  │     └─ uploader_id = 42 (current user_id) ✓
│  │
│  ├─ Check chapter number not duplicate ✓
│  │  └─ SELECT COUNT(*) FROM chapters
│  │     WHERE manga_id=150 AND chapter_num=4
│  │     └─ COUNT = 0 ✓ (New chapter number)
│  │
│  ├─ Validate PDF file ✓
│  │  └─ Extension is .pdf ✓
│  │  └─ File size < MAX_SIZE ✓
│  │
│  └─ Confirm chapter_num is positive integer ✓
│
├─ File Processing Phase
│  │
│  └─ PDF File:
│     ├─ secure_filename("chapter4.pdf")
│     ├─ Generate unique name: "pdf_1702656200_789.pdf"
│     ├─ Save to: static/books/pdf_1702656200_789.pdf
│     └─ pdf_filename = "pdf_1702656200_789.pdf"
│
├─ Database Insert Phase
│  │
│  └─ SQL Query (INSERT INTO chapters):
│     INSERT INTO chapters (
│       manga_id,
│       chapter_num,
│       title,
│       pdf_filename,
│       created_at
│     ) VALUES (
│       150,  ← Manga series id
│       4,    ← Chapter number
│       'The Turning Point',  ← Chapter title
│       'pdf_1702656200_789.pdf',
│       DATETIME('now')
│     )
│
│     Result: chapter id = 504
│     ✓ UNIQUE constraint satisfied (150, 4) is unique
│
├─ Flash Message
│  └─ "Chapter uploaded successfully!"
│
├─ Redirect
│  └─ HTTP 302 → /manga/150/upload-chapter
│     (Refresh page showing updated chapter list)
│
└─ Display Result
   │
   ├─ Updated Chapter List:
   │  ├─ Chapter 1: "Chapter 1"
   │  ├─ Chapter 2: "The Beginning"
   │  ├─ Chapter 3: "Rising Tension"
   │  └─ Chapter 4: "The Turning Point"  ← NEW!
   │
   ├─ Reader Notification:
   │  └─ /manga/150 page now shows "4 chapters"
   │
   └─ Readers can access:
      └─ GET /manga/150/chapter/504 → Read Chapter 4

```

---

## 6. Reading History & Watchlist Flow

```
READER INTERACTS WITH CONTENT
↓
┌─────────────────────────────────────────┐
│  GET /book/<id> or /manga/<id>         │
│  (Read Book/Manga)                     │
└─────────────────────────────────────────┘
│
├─ [Action 1] Reading Content
│  │
│  ├─ User opens book/manga
│  ├─ JavaScript tracks viewing time
│  ├─ Session tracks user_id
│  │
│  └─ No immediate database insert
│     (Can implement auto-save on page exit)
│
├─ [Action 2] Add to Watchlist
│  │
│  ├─ User clicks "♡ Add to Watchlist" button
│  │
│  └─ AJAX POST /api/add_to_watchlist
│     Request: { book_id: 101 }
│     │
│     ├─ Verify user authenticated
│     ├─ Check book exists
│     └─ INSERT INTO watchlist
│        (
│          user_id = session['user_id'],
│          book_id = 101,
│          created_at = DATETIME('now')
│        )
│        │
│        └─ Return JSON: { success: true }
│           │
│           ├─ Button changes to "♥ Remove from Watchlist"
│           └─ Visual feedback (heart fills)
│
├─ [Action 3] View Watchlist
│  │
│  └─ User clicks "My Watchlist" link
│     │
│     ├─ GET /watchlist
│     │
│     ├─ Query Database:
│     │  SELECT b.*, w.created_at
│     │  FROM watchlist w
│     │  JOIN books b ON w.book_id = b.id
│     │  WHERE w.user_id = ?
│     │  ORDER BY w.created_at DESC
│     │
│     ├─ Render watchlist.html with results
│     │
│     └─ Display all bookmarked items
│        ├─ Book covers
│        ├─ Titles & authors
│        ├─ Added date
│        └─ Quick action links
│
├─ [Action 4] Track Reading History
│  │
│  └─ (Manual logging option)
│     User clicks "Mark as Read" button
│     │
│     └─ POST /api/mark_read
│        INSERT INTO history
│        (
│          user_id = session['user_id'],
│          book_id = 101,
│          date_read = TODAY()
│        )
│        │
│        └─ Flash: "Added to reading history"
│
└─ [Action 5] View Profile Statistics
   │
   └─ GET /profile
      │
      ├─ Query Database:
      │  SELECT COUNT(*) FROM history WHERE user_id = ?
      │  SELECT COUNT(*) FROM watchlist WHERE user_id = ?
      │
      ├─ Render profile.html with stats
      │
      └─ Display:
         ├─ Total books read
         ├─ Watchlist count
         ├─ Recent reading activity
         └─ Latest uploads (if publisher)

```

---

## 7. Admin Workflow

```
ADMIN LOGS IN
↓
GET /admin/users or /admin/team or /admin/ai_summaries
↓
┌──────────────────────────────────────────────────────────┐
│          ADMIN DASHBOARD LOADED                          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ [User Management] [Team Management] [AI Cache]      │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ ┌─ User Management (/admin/users) ──────────────────┐ │
│ │                                                   │ │
│ │ All Users Table:                                 │ │
│ │ ┌────────────────────────────────────────────┐  │ │
│ │ │ ID │ Username │ Role      │ Status │ Actions│  │ │
│ │ ├────────────────────────────────────────────┤  │ │
│ │ │ 1  │ admin1   │ admin     │ active │ [▼]   │  │ │
│ │ │ 2  │ john     │ publisher │ active │ [Ban] │  │ │
│ │ │ 3  │ jane     │ reader    │ banned │[Unban]│  │ │
│ │ │ 4  │ mike     │ reader    │ active │ [Ban] │  │ │
│ │ └────────────────────────────────────────────┘  │ │
│ │                                                   │ │
│ │ Pending Role Requests:                           │ │
│ │ ┌────────────────────────────────────────────┐  │ │
│ │ │ john_doe → publisher [Approve][Reject]     │  │ │
│ │ │ jane_doe → publisher [Approve][Reject]     │  │ │
│ │ └────────────────────────────────────────────┘  │ │
│ │                                                   │ │
│ └─────────────────────────────────────────────────┘ │
│                                                          │
│ ┌─ Team Management (/admin/team) ───────────────────┐ │
│ │                                                   │ │
│ │ Add New Team Member:                             │ │
│ │ ┌────────────────────────────────────────────┐  │ │
│ │ │ Full Name: [John Developer         ]       │  │ │
│ │ │ Role:      [Developer            ▼]       │  │ │
│ │ │ Bio:       [Expert in Flask      ]        │  │ │
│ │ │ Avatar:    [Choose File...              ]  │  │ │
│ │ │            [+ Add Member]                 │  │ │
│ │ └────────────────────────────────────────────┘  │ │
│ │                                                   │ │
│ │ Team Members List:                               │ │
│ │ ┌────────────────────────────────────────────┐  │ │
│ │ │ [JD] John Developer - Developer             │  │ │
│ │ │      Expert in Flask (Delete)               │  │ │
│ │ │ [SA] Sarah Admin - Project Manager          │  │ │
│ │ │      Leads the team (Delete)                │  │ │
│ │ └────────────────────────────────────────────┘  │ │
│ │                                                   │ │
│ └─────────────────────────────────────────────────┘ │
│                                                          │
│ ┌─ AI Cache Management (/admin/ai_summaries) ──────┐ │
│ │                                                   │ │
│ │ Cached Summaries:                                │ │
│ │ ┌────────────────────────────────────────────┐  │ │
│ │ │ Type    │ Item      │ Model    │ Date     │  │ │
│ │ ├────────────────────────────────────────────┤  │ │
│ │ │ chapter │ Manga 6   │ gpt-3.5  │ 2024-01 │  │ │
│ │ │ book    │ Book 42   │ gpt-3.5  │ 2024-01 │  │ │
│ │ │ chapter │ Manga 8   │ gpt-3.5  │ 2024-01 │  │ │
│ │ └────────────────────────────────────────────┘  │ │
│ │                                                   │ │
│ │ [Clear All Cache]  [Search...]                   │ │
│ │                                                   │ │
│ └─────────────────────────────────────────────────┘ │
│                                                          │
└──────────────────────────────────────────────────────────┘

ADMIN ACTIONS:

┌─ Ban User Action ─────────────────────────────────────┐
│ Admin clicks [Ban] next to user "john"               │
│ ↓                                                    │
│ POST /admin/users/<user_id>/ban                     │
│ ↓                                                    │
│ Backend:                                            │
│ ├─ Verify admin role ✓                              │
│ ├─ Prevent self-ban ✓                               │
│ ├─ Prevent banning other admins ✓                   │
│ └─ UPDATE users SET status='banned' WHERE id=?      │
│                                                     │
│ Next Request from "john":                           │
│ ├─ @before_request: check_banned()                  │
│ ├─ Query: SELECT status FROM users WHERE id=john    │
│ ├─ Found: status='banned'                           │
│ ├─ session.clear()                                  │
│ ├─ flash("Your account has been banned.")           │
│ └─ redirect(/login)                                 │
│ ↓                                                    │
│ "john" is logged out and cannot access protected    │
│ routes                                              │
└──────────────────────────────────────────────────────┘

┌─ Approve Publisher Request ───────────────────────────┐
│ Admin clicks [Approve] for role request              │
│ ↓                                                    │
│ POST /admin/users/approve/<req_id>                  │
│ ↓                                                    │
│ Backend:                                            │
│ ├─ Query role_requests table:                        │
│ │  SELECT user_id, requested_role                   │
│ │  FROM role_requests WHERE id=? AND status='pending'│
│ │  ↓ Result: user_id=5, requested_role='publisher'  │
│ │                                                    │
│ ├─ Update user role:                                │
│ │  UPDATE users SET role='publisher' WHERE id=5     │
│ │                                                    │
│ ├─ Mark request as approved:                        │
│ │  UPDATE role_requests SET status='approved'       │
│ │  WHERE id=?                                       │
│ │                                                    │
│ └─ flash("User upgraded to publisher.")             │
│                                                     │
│ User "john_doe" can now:                            │
│ ├─ Access /add (upload books/manga)                │
│ ├─ Access /my_uploads (publisher dashboard)         │
│ └─ Upload chapters to manga series                 │
└──────────────────────────────────────────────────────┘

```

---

## 8. Modern Manga Reader Interface

```
┌────────────────────────────────────────────────────────────────┐
│                  MODERN MANGA READER UI                        │
│                 /manga/<id> (manga_reader_new.html)            │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ╔════════════════════════════════════════════════════════╗   │
│  ║ Chapter 1: The Beginning  [AI INSIGHTS]  [⚙️] [🚩] [☰] ║   │
│  ╚════════════════════════════════════════════════════════╝   │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    │
│                                                                │
│  ┌─────────────────────────────────┬──────────────────────┐   │
│  │                                 │                      │   │
│  │                                 │  ┌──────────────────┐│   │
│  │                                 │  │  AI CHATBOT      ││   │
│  │      MANGA PAGE VIEWER          │  ├──────────────────┤│   │
│  │                                 │  │ CHATBOT│TRANSLATE││   │
│  │    ┌─────────────────────────┐  │  ├──────────────────┤│   │
│  │    │                         │  │  │ [Toggle ON] [⊙]  ││   │
│  │    │    PAGE IMAGE AREA      │  │  │                  ││   │
│  │    │                         │  │  │ Hi! Ask me about ││   │
│  │    │    (Placeholder or      │  │  │ this chapter...  ││   │
│  │    │     actual image)       │  │  │ [Chat window]    ││   │
│  │    │                         │  │  └──────────────────┘│   │
│  │    │                         │  │                      │   │
│  │    │                         │  │  ┌──────────────────┐│   │
│  │    │                         │  │  │ AI ASSISTANT     ││   │
│  │    │                         │  │  ├──────────────────┤│   │
│  │    │                         │  │  │ Smart Summary:   ││   │
│  │    │                         │  │  │ • Protagonist    ││   │
│  │    │                         │  │  │   meets ally     ││   │
│  │    │                         │  │  │ • Battle begins  ││   │
│  │    │                         │  │  │ • Plot twist     ││   │
│  │    │                         │  │  │ [VIEW FULL]      ││   │
│  │    │                         │  │  └──────────────────┘│   │
│  │    │                         │  │                      │   │
│  │    │                         │  │  ┌──────────────────┐│   │
│  │    │                         │  │  │ CHARACTER INFO   ││   │
│  │    │                         │  │  ├──────────────────┤│   │
│  │    │                         │  │  │ [🔵] Protagonist││   │
│  │    │                         │  │  │      Hero Main   ││   │
│  │    │                         │  │  │ [🔵] Ally        ││   │
│  │    │                         │  │  │      Support ♪   ││   │
│  │    │                         │  │  │ [🔵] Villain     ││   │
│  │    │                         │  │  │      Antagonist  ││   │
│  │    │                         │  │  │ [Show More]      ││   │
│  │    │                         │  │  └──────────────────┘│   │
│  │    └─────────────────────────┘  │                      │   │
│  │                                 │                      │   │
│  │  [PREV] ═════[Slider]═════[NEXT]                      │   │
│  │  Page 15/120                                          │   │
│  │                                 │                      │   │
│  └─────────────────────────────────┴──────────────────────┘   │
│                                                                │
│  Colors:                                                       │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ Background:    #1a1a2e (Dark Navy)                    │  │
│  │ Accent:        #00d4ff (Cyan Glow)                    │  │
│  │ Text:          #e0e0e0 (Light Gray)                   │  │
│  │ Cards:         #0f3460 (Dark Blue)                    │  │
│  │ Borders:       Cyan with glow effect                  │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
└────────────────────────────────────────────────────────────────┘

INTERACTIVE FEATURES:

1. Navigation Controls
   ├─ [PREV] button → previousPage()
   ├─ Progress Slider → Jump to any page percentage
   ├─ [NEXT] button → nextPage()
   └─ Page Counter → "Page X/Y" display

2. Settings Modal (⚙️ button)
   ├─ Reading Mode
   │  ├─ Single page
   │  ├─ Double page
   │  ├─ Vertical scroll
   │  └─ Horizontal scroll
   ├─ Background
   │  ├─ Light
   │  ├─ Dark (default)
   │  └─ Sepia
   ├─ Brightness Slider (0-200%)
   ├─ Font Size
   │  ├─ Small
   │  ├─ Medium
   │  └─ Large
   └─ [Save Settings] → localStorage

3. AI Features (Right Sidebar)
   ├─ AI Chatbot
   │  ├─ Ask questions about manga
   │  ├─ Real-time responses
   │  └─ Translation tab
   ├─ Smart Summary
   │  ├─ Auto-generated overview
   │  ├─ 3 key bullet points
   │  └─ [VIEW FULL ANALYSIS]
   └─ Character Profiles
      ├─ Avatar circles
      ├─ Character names
      ├─ Traits/roles
      ├─ Voice actor info
      └─ [Show More]

4. User Actions
   ├─ 🚩 Report Issue → POST /report_manga
   ├─ ☰ Menu (Mobile) → Navigation drawer
   └─ Add to Watchlist → POST /api/add_to_watchlist

```

---

## 9. Manga Reader Data Loading Flow

```
User Navigates to /manga/<id>
│
├─ Route Handler: @app.route("/manga/<int:id>")
│  │
│  ├─ Verify user authenticated (optional for manga reading)
│  │
│  ├─ Query manga metadata:
│  │  SELECT * FROM books WHERE id=? AND book_type='manga'
│  │  ↓ Gets: title, author, cover, description
│  │
│  ├─ Get chapter list:
│  │  SELECT * FROM chapters WHERE manga_id=? ORDER BY chapter_num
│  │  ↓ Gets: Chapter 1, 2, 3... with PDFs
│  │
│  ├─ Get first chapter pages:
│  │  API call: /api/chapter/<chapter_id>/pages
│  │  ↓ Returns: Array of page image URLs
│  │
│  ├─ Get character profiles:
│  │  API call: /api/manga/<id>/characters
│  │  ↓ Returns: Array of character objects
│  │
│  ├─ Get AI summary (if cached):
│  │  Query: SELECT * FROM ai_summaries WHERE item_type='chapter'
│  │  ↓ If not cached: POST /ai_summary to generate
│  │
│  └─ Render template: manga_reader_new.html
│     ├─ Pass: manga data, chapters, characters, AI summary
│     └─ Return: HTML page with all data embedded
│
├─ Browser receives HTML
│  │
│  ├─ JavaScript initializes:
│  │  ├─ Load localStorage settings
│  │  ├─ Apply saved preferences
│  │  ├─ Setup event listeners
│  │  ├─ Initialize page slider
│  │  └─ Load first page image
│  │
│  └─ Page is interactive and ready
│
├─ User Interactions
│  │
│  ├─ [NEXT] button clicked
│  │  ├─ JavaScript: currentPage++
│  │  ├─ Update image src
│  │  ├─ Update page counter
│  │  ├─ API: /api/chapter/<id>/pages?page=N (if needed)
│  │  └─ Display new page
│  │
│  ├─ Change Chapter
│  │  ├─ User selects chapter from dropdown
│  │  ├─ API: /api/manga/<id>/chapters
│  │  ├─ Load new chapter pages
│  │  ├─ Reset page counter
│  │  └─ Display first page of new chapter
│  │
│  ├─ AI INSIGHTS clicked
│  │  ├─ Modal opens with AI summary
│  │  ├─ Display smart summary (3 bullet points)
│  │  ├─ Show character profiles
│  │  └─ Enable AI chatbot tab
│  │
│  ├─ Settings (⚙️) clicked
│  │  ├─ Modal opens with options
│  │  ├─ User adjusts preferences
│  │  ├─ [Save Settings] clicked
│  │  ├─ JavaScript: localStorage.setItem('settings', JSON.stringify(...))
│  │  ├─ Apply CSS changes to page
│  │  └─ Modal closes
│  │
│  └─ 🚩 Report Issue clicked
│     ├─ Modal opens with report form
│     ├─ User enters issue description
│     ├─ POST /report_manga { manga_id, reason }
│     ├─ Backend stores in database
│     ├─ Admin notified
│     └─ User receives confirmation
│
└─ Session tracks activity (reading history)

```

---

## 10. Database Relationship Diagram

```
                    ┌──────────────────┐
                    │     users        │
                    ├──────────────────┤
                    │ id (PK)          │
                    │ username (UQ)    │
                    │ email (UQ)       │
                    │ password         │
                    │ role             │ ◄─────────┐
                    │ status           │           │
                    └──────────────────┘           │
                          ▲                        │
                          │ 1                      │
                    ┌─────┴──────────┐             │
                    │ (Foreign Key)  │             │
                    │ uploader_id    │ Many       │
                    │                │            │
                    ▼ Many           │            │
            ┌──────────────────────┐ │  ┌─────────┴────────┐
            │      books           │─┤  │ role_requests    │
            ├──────────────────────┤ │  ├──────────────────┤
            │ id (PK)              │ │  │ id (PK)          │
            │ title                │ │  │ user_id (FK)─────┘
            │ author               │ │  │ requested_role   │
            │ category             │ │  │ status           │
            │ pdf_filename         │ │  └──────────────────┘
            │ audio_filename       │ │
            │ cover_path           │ │  ┌──────────────────┐
            │ description          │ │  │  watchlist       │
            │ book_type            │ │  ├──────────────────┤
            │ uploader_id (FK)─────┘ │  │ id (PK)          │
            │ created_at           │    │ user_id (FK)─────┘
            └──────────────────────┘    │ book_id (FK)──┐
                    │ 1                 │ created_at    │
                    │                   └──────────────┘│
                    │ Many                              │
                    ▼                        ┌──────────┴──────┐
            ┌──────────────────────┐        │                │
            │    chapters          │        │  ┌─────────────┴──┐
            ├──────────────────────┤        │  │    history     │
            │ id (PK)              │        │  ├────────────────┤
            │ manga_id (FK)────────┘        │  │ id (PK)        │
            │ chapter_num          │           │ user_id (FK)───┘
            │ title                │        │  │ book_id (FK)───┐
            │ pdf_filename         │        │  │ date_read      │
            │ created_at           │        │  └────────────────┘
            │ UNIQUE(manga_id,     │        │
            │   chapter_num)       │        │
            └──────────────────────┘        │
                                           │
            ┌──────────────────────┐        │
            │   ai_summaries       │        │
            ├──────────────────────┤        │
            │ id (PK)              │        │
            │ item_type            │        │
            │ item_id ────────────────────┘
            │ summary              │
            │ model                │
            │ created_at           │
            │ UNIQUE(item_type,    │
            │   item_id)           │
            └──────────────────────┘

            ┌──────────────────────┐
            │      team            │
            ├──────────────────────┤
            │ id (PK)              │
            │ full_name            │
            │ role                 │
            │ bio                  │
            │ avatar_path          │
            │ initials             │
            │ created_at           │
            └──────────────────────┘

KEY:
─ PK  = Primary Key
─ FK  = Foreign Key
─ UQ  = Unique Constraint
─ 1 to Many relationship shown with ├─────────┴──────┐

```

---

This comprehensive visual guide covers:
✅ System architecture (layered design)
✅ User journey (authentication to actions)
✅ Book upload workflow (files & database)
✅ Manga upload workflow (series + first chapter)
✅ Chapter management (incremental uploads)
✅ Reader interaction (watchlist & history)
✅ Admin operations (user management, approvals, cache)
✅ Modern reader UI (layout & features)
✅ Data loading flow (API calls & rendering)
✅ Database relationships (normalized schema)

