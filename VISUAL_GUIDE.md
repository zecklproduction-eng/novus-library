# Visual Guide: Dual-Mode Upload & Chapter Management

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    ADD NEW CONTENT PAGE (/add)                   │
│                                                                   │
│  ┌──────────────────────┬──────────────────────┐                │
│  │  📚 BOOK TAB         │  🎨 MANGA TAB        │                │
│  │  (Currently Active)  │  (Inactive)          │                │
│  └──────────────────────┴──────────────────────┘                │
│                                                                   │
│  BOOK FORM:                                                      │
│  ├─ Title (required)                                            │
│  ├─ Author (required)                                           │
│  ├─ Category (dropdown)                                         │
│  ├─ Description (textarea)                                      │
│  ├─ PDF File (drag & drop - required)                          │
│  ├─ Audio File (drag & drop - optional)                        │
│  └─ Cover Image (required)                                      │
│     └─ [PUBLISH BOOK]                                          │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│              MANGA FORM (When Manga Tab Selected)                │
│                                                                   │
│  ├─ Manga Title (required)                                      │
│  ├─ Author/Artist (required)                                    │
│  ├─ Category (dropdown)                                         │
│  ├─ Publishing Status (Ongoing/Completed/Hiatus)               │
│  ├─ Description (textarea)                                      │
│  ├─ Cover Image (required)                                      │
│  ├─ Chapter 1 PDF (drag & drop - required)                     │
│  └─ [CREATE MANGA SERIES]                                       │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Upload Flow Diagram

### BOOK FLOW:
```
Upload Form (/add)
    ↓
Validate inputs
    ↓
Save PDF → static/books/
Save Audio → static/audio/
Save Cover → static/covers/
    ↓
INSERT INTO books (
    title, author, category, 
    pdf_filename, audio_filename, 
    cover_path, book_type='book'
)
    ↓
Redirect to home
    ↓
Shows in: / (home page - books only)
```

### MANGA FLOW:
```
Upload Form (/add)
    ↓
Validate inputs
    ↓
Save Cover → static/covers/
Save Chapter 1 PDF → static/books/
    ↓
INSERT INTO books (
    title, author, category,
    cover_path, description,
    book_type='manga'
)
    ↓
Get manga_id (lastrowid)
    ↓
INSERT INTO chapters (
    manga_id, chapter_num=1,
    title, pdf_filename
)
    ↓
Redirect to /manga
    ↓
Shows in: /manga (manga page only)
```

## Chapter Management Flow

```
My Uploads Dashboard (/my_uploads)
    ↓
    └─ For Each Manga:
        ├─ Shows: Title, Author, Cover
        ├─ Shows: "X chapters" badge
        └─ Button: [+ Chapter]
            ↓
            └─ Upload Chapter Form (/manga/<id>/upload-chapter)
                ├─ GET: Show existing chapters + upload form
                │   ├─ Existing Chapters (grid layout):
                │   │  ├─ Chapter 1
                │   │  ├─ Chapter 2
                │   │  └─ Chapter 3
                │   │
                │   └─ Upload New Chapter:
                │      ├─ Chapter Number* (input)
                │      ├─ Chapter Title (optional)
                │      ├─ PDF File (drag & drop)*
                │      └─ [UPLOAD CHAPTER]
                │
                └─ POST: Validate & Save
                    ├─ Validate chapter number is unique
                    ├─ Save PDF → static/books/
                    └─ INSERT INTO chapters (
                         manga_id, chapter_num,
                         title, pdf_filename
                       )
                        ↓
                        └─ Redirect to same form with success message
```

## Database Schema Relationships

```
┌─────────────────────┐
│      books          │
├─────────────────────┤
│ id (PK)            │
│ title              │
│ author             │
│ category           │
│ description        │
│ cover_path         │
│ pdf_filename       │ ← For books only
│ audio_filename     │ ← For books only
│ book_type          │ ← 'book' or 'manga'
│ uploader_id (FK)   │
│ created_at         │
└─────────────────────┘
        ↑
        │ 1:Many
        │
┌─────────────────────┐
│     chapters        │
├─────────────────────┤
│ id (PK)            │
│ manga_id (FK) ─────┤
│ chapter_num        │
│ title              │
│ pdf_filename       │
│ created_at         │
│ UNIQUE(manga_id,   │
│  chapter_num)      │
└─────────────────────┘
```

## URL Routing Map

```
GET  /add                          → Show add_book.html (dual-mode form)
POST /add                          → Handle book/manga upload

GET  /my_uploads                   → Show user's uploads (books + manga)

GET  /manga/<id>/upload-chapter    → Show chapter upload form
POST /manga/<id>/upload-chapter    → Handle chapter upload

GET  /manga                        → List all manga series
GET  /manga/read/<id>              → Read/view manga with chapters
```

## Data Flow Example: Adding "Sword Art Online" Manga

### Step 1: Create Manga Series
```
Form Submission (/add POST):
├─ title: "Sword Art Online"
├─ author: "Reki Kawahara"
├─ category: "Sci-Fi"
├─ status: "ongoing"
├─ description: "A story about virtual reality..."
├─ cover_image: uploaded → saved as "sao_cover.jpg"
├─ chapter_file: uploaded → saved as "sao_ch1.pdf"
└─ book_type: "manga"

Database Operations:
├─ INSERT INTO books VALUES (
│   NULL, 'Sword Art Online', 'Reki Kawahara',
│   'Sci-Fi', 'A story about...', 'covers/sao_cover.jpg',
│   'manga', 2024-12-19 14:30:00
│ ) → books.id = 5
│
└─ INSERT INTO chapters VALUES (
    NULL, 5, 1, 'Chapter 1',
    'sao_ch1.pdf', 2024-12-19 14:30:00
  )

Result:
├─ Manga now appears on /manga page
├─ Can be viewed at /manga/read/5
└─ Shows: "1 chapter"
```

### Step 2: Add Chapter 2
```
Form Submission (/manga/5/upload-chapter POST):
├─ chapter_num: 2
├─ chapter_title: "The Grand Quest Begins"
├─ chapter_file: uploaded → saved as "sao_ch2.pdf"

Validation:
├─ Check: manga_id=5 exists ✓
├─ Check: chapter_num=2 unique for manga 5 ✓
└─ Check: File is PDF ✓

Database:
└─ INSERT INTO chapters VALUES (
    NULL, 5, 2, 'The Grand Quest Begins',
    'sao_ch2.pdf', 2024-12-19 15:45:00
  )

Result:
├─ My Uploads shows: "2 chapters"
├─ Chapter list shows: Chapter 1, Chapter 2
└─ Both chapters ordered numerically
```

### Step 3: Add Chapter 5 (Skipping 3, 4)
```
Form Submission:
├─ chapter_num: 5
├─ chapter_title: "The Return"
└─ chapter_file: "sao_ch5.pdf"

Result:
├─ Chapter appears with number 5
├─ Chapter list now shows: 1, 2, 5
└─ NOTE: Gaps are allowed (chapters don't need to be sequential)
```

## User Interface Mockup

```
ADD CONTENT PAGE:
═══════════════════════════════════════════════════════════════
  📚 Book          🎨 Manga                    ← TAB BUTTONS
──────────────────────────────────────────────────────────────
MANGA TAB (when selected):
  ┌──────────────────────────────────────────────────────────┐
  │ Add New Content                                           │
  │                                                            │
  │ Title:          [_____________________]                  │
  │ Author/Artist:  [_____________________]                  │
  │ Category:       [▼ Select Category _____]                │
  │ Status:         [▼ Ongoing ___________]                  │
  │ Description:    [________multiline text field______]     │
  │                                                            │
  │ ┌─ First Chapter ──────────────────────────────────────┐ │
  │ │ Chapter 1 PDF:  [DROP HERE OR BROWSE] ✓ file.pdf   │ │
  │ └──────────────────────────────────────────────────────┘ │
  │                                                            │
  │        Cover Image:    [UPLOAD]                           │
  │        ┌─────────────┐                                   │
  │        │   PREVIEW   │                                   │
  │        │   AREA      │                                   │
  │        └─────────────┘                                   │
  │                                                            │
  │                  [CREATE MANGA SERIES]                   │
  └──────────────────────────────────────────────────────────┘
```

## My Uploads Dashboard Mockup

```
MY UPLOADS:
═════════════════════════════════════════════════════════════════
  5 items found

  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
  │ 📚 BOOK     │  │ 🎨 MANGA    │  │ 🎨 MANGA    │
  │             │  │   MANGA     │  │   MANGA     │
  │ Harry       │  │ Sword Art   │  │ Attack on   │
  │ Potter      │  │ Online      │  │ Titan       │
  │             │  │             │  │             │
  │ Author:     │  │ Author:     │  │ Author:     │
  │ J.K.        │  │ Reki        │  │ Hajime      │
  │ Rowling     │  │ Kawahara    │  │ Isayama     │
  │             │  │             │  │             │
  │ Category:   │  │ Category:   │  │ Category:   │
  │ Fantasy     │  │ Sci-Fi      │  │ Action      │
  │             │  │             │  │             │
  │             │  │ 📄 5 ch     │  │ 📄 15 ch    │
  │             │  │             │  │             │
  │ [View]      │  │[+ Ch][View] │  │[+ Ch][View] │
  │ [Edit]      │  │[Edit][Del]  │  │[Edit][Del]  │
  │ [Delete]    │  │             │  │             │
  └─────────────┘  └─────────────┘  └─────────────┘
```

## Chapter Upload Page Mockup

```
ADD CHAPTER (for "Sword Art Online"):
═════════════════════════════════════════════════════════════════
  ← Back to Manga

  ➕ Add Chapter
  Sword Art Online by Reki Kawahara

  ┌─────────────────────────────────────────────────────────────┐
  │ EXISTING CHAPTERS (5)                                        │
  │                                                              │
  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐│
  │  │   1    │  │   2    │  │   3    │  │   4    │  │   5    ││
  │  │Chapter │  │The Gr  │  │Return  │  │Rise    │  │Quest   ││
  │  │  One   │  │begins  │  │        │  │        │  │        ││
  │  └────────┘  └────────┘  └────────┘  └────────┘  └────────┘│
  │                                                              │
  └─────────────────────────────────────────────────────────────┘

  UPLOAD NEW CHAPTER:
  ┌─────────────────────────────────────────────────────────────┐
  │ Chapter Number*:    [_6_]  (must be unique)                │
  │ Chapter Title:      [Optional - e.g., "New Beginning"]     │
  │                                                              │
  │ PDF File*:          [DRAG & DROP OR BROWSE]                │
  │                     📄 file.pdf                             │
  │                                                              │
  │              [UPLOAD CHAPTER]                              │
  └─────────────────────────────────────────────────────────────┘
```

---

This visual guide shows how the dual-mode upload system and chapter management work together to provide a seamless experience for publishers managing both books and manga series.
