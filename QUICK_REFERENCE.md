# Quick Reference Card: Dual-Mode Upload & Chapter System

## 🚀 Quick Start

### For Publishers/Admins
```
1. Go to http://localhost:5000/add
2. Choose "Book" or "Manga" tab
3. Fill form and upload files
4. Done! Content appears on site
```

---

## 📋 Routes & URLs

| Route | Method | Purpose |
|-------|--------|---------|
| `/add` | GET | Show upload form |
| `/add` | POST | Process upload (book/manga) |
| `/manga/<id>/upload-chapter` | GET | Show chapter upload form |
| `/manga/<id>/upload-chapter` | POST | Upload chapter |
| `/my_uploads` | GET | Show user's uploads |
| `/manga` | GET | List all manga |
| `/manga/read/<id>` | GET | Read manga |
| `/book/<id>` | GET | View book |

---

## 📝 Form Fields

### Book Upload
```
Title*              - Text input
Author*             - Text input
Category*           - Dropdown
Description         - Text area
PDF File*           - File upload
Audio File          - File upload (optional)
Cover Image*        - Image upload
```

### Manga Upload
```
Manga Title*        - Text input
Author/Artist*      - Text input
Category*           - Dropdown
Status*             - Dropdown (Ongoing/Completed/Hiatus)
Description         - Text area
Cover Image*        - Image upload
Chapter 1 PDF*      - File upload
```

### Chapter Upload
```
Chapter Number*     - Integer input
Chapter Title       - Text input (optional)
PDF File*           - File upload
```

---

## 🗄️ Database Schema Quick View

### books table
```
id              - Integer (Primary Key)
title           - Text
author          - Text
category        - Text
pdf_filename    - Text
audio_filename  - Text
cover_path      - Text
description     - Text
book_type       - Text ('book' or 'manga')
uploader_id     - Integer (Foreign Key)
created_at      - DateTime
```

### chapters table
```
id              - Integer (Primary Key)
manga_id        - Integer (Foreign Key → books.id)
chapter_num     - Integer
title           - Text
pdf_filename    - Text
created_at      - DateTime

UNIQUE(manga_id, chapter_num)  - No duplicate chapters
```

---

## 💾 File Storage Locations

| Content Type | Folder | Extension |
|--------------|--------|-----------|
| Book PDFs | `/static/books/` | .pdf |
| Chapters | `/static/books/` | .pdf |
| Audio | `/static/audio/` | .mp3 |
| Covers | `/static/covers/` | .jpg, .png |

---

## 🔐 Authorization

### Required Roles for Upload
- **Admin** ✅ Can upload anything
- **Publisher** ✅ Can upload anything
- **Reader** ❌ Cannot upload

### Required Roles for View
- **All authenticated users** ✅ Can view

---

## 🎨 UI Components

### Tab Interface
```html
<button onclick="switchTab('book')">Book</button>
<button onclick="switchTab('manga')">Manga</button>
```

### File Upload Zone
```
[DRAG & DROP AREA OR BROWSE]
Shows file name after selection: ✓ filename.pdf
```

### Dashboard Features
```
Books:  📚 BOOK ICON | View | Edit | Delete
Manga:  🎨 MANGA ICON | "5 chapters" | +Chapter | View | Edit | Delete
```

---

## ✅ Validation Rules

### Book Upload
- [x] Title is required
- [x] PDF file is required
- [x] Cover image is required
- [x] File types: .pdf, .mp3, .jpg/.png

### Manga Creation
- [x] Title is required
- [x] Cover image is required
- [x] Chapter 1 PDF is required
- [x] Status must be valid

### Chapter Upload
- [x] Chapter number is required
- [x] Chapter number must be unique per manga
- [x] PDF file is required
- [x] Chapter number must be positive integer

---

## 🧪 Test Commands

### Check if tables exist
```sql
SELECT name FROM sqlite_master WHERE type='table';
```

### View all manga
```sql
SELECT id, title, author, book_type FROM books WHERE book_type='manga';
```

### View chapters for manga ID 5
```sql
SELECT * FROM chapters WHERE manga_id=5 ORDER BY chapter_num;
```

### Count chapters
```sql
SELECT manga_id, COUNT(*) as chapter_count FROM chapters GROUP BY manga_id;
```

---

## 🐛 Quick Debugging

### Issue: Tab doesn't switch
```javascript
// Check browser console: F12 → Console
// Look for JavaScript errors
// Verify IDs: bookTab, mangaTab, type-tab
```

### Issue: Chapter doesn't save
```python
# Add print statements in upload_chapter() route
# Check: manga_id exists
# Check: chapter_num is unique
# Check: PDF file saved to disk
```

### Issue: Dashboard shows no chapters
```python
# Verify query: c.execute("SELECT COUNT(*) FROM chapters WHERE manga_id=?")
# Check: manga_chapters dictionary populated
# Check: template variable passed correctly
```

---

## 📱 File Size Limits

| File Type | Max Size |
|-----------|----------|
| Book PDF | 50 MB |
| Chapter PDF | 50 MB |
| Audio MP3 | 100 MB |
| Cover Image | 5 MB |

---

## 🔄 Data Flow Diagram

```
ADD BOOK FLOW:
Form → Validate → Save Files → Insert books → Redirect /

ADD MANGA FLOW:
Form → Validate → Save Files → Insert books → Insert chapter → Redirect /manga

ADD CHAPTER FLOW:
Form → Validate → Save PDF → Insert chapter → Reload page
```

---

## 📞 Common Tasks

### Add a book
```
1. Click: /add
2. Select: Book tab
3. Fill: Title, Author, Category, Description
4. Upload: PDF, Audio (optional), Cover
5. Click: PUBLISH BOOK
```

### Add a manga
```
1. Click: /add
2. Select: Manga tab
3. Fill: Title, Author, Category, Status, Description
4. Upload: Cover, Chapter 1 PDF
5. Click: CREATE MANGA SERIES
```

### Add chapter to manga
```
1. Go: /my_uploads
2. Find: Manga series
3. Click: + Chapter
4. Enter: Chapter number
5. Upload: PDF
6. Click: UPLOAD CHAPTER
```

---

## 🎯 Form Submission Values

### Book Upload
```
book_type = 'book'
pdf_file = [File object]
audio_file = [File object] (optional)
cover_image = [File object]
```

### Manga Upload
```
book_type = 'manga'
cover_image = [File object]
chapter_file = [File object]
status = 'ongoing' | 'completed' | 'hiatus'
```

### Chapter Upload
```
chapter_num = [Integer]
chapter_title = [String] (optional)
chapter_file = [File object]
```

---

## 💡 Tips & Tricks

1. **Chapter Numbers**: Can skip (e.g., 1, 2, 5, 7 is valid)
2. **Chapter Titles**: Auto-generated if blank (e.g., "Chapter 2")
3. **Dashboard**: Shows chapter count for manga only
4. **Manga vs Books**: `book_type` column determines type
5. **File Names**: Automatically sanitized for safety

---

## 🚨 Error Messages

| Error | Cause | Fix |
|-------|-------|-----|
| "Title is required" | Empty title field | Fill in title |
| "Chapter X already exists" | Duplicate chapter number | Use different number |
| "Chapter file must be a PDF" | Wrong file type | Upload .pdf file |
| "Manga not found" | Invalid manga ID | Check URL |
| "You cannot access this" | Wrong user/role | Login as admin/publisher |

---

## 📊 Database Queries Reference

### Create test book
```sql
INSERT INTO books VALUES (NULL, 'Test Book', 'Author', 'Fiction', 'test.pdf', NULL, 'cover.jpg', NULL, 'book', 1, datetime('now'));
```

### Create test manga
```sql
INSERT INTO books VALUES (NULL, 'Test Manga', 'Artist', 'Action', NULL, NULL, 'cover.jpg', 'Description', 'manga', 1, datetime('now'));
```

### Create test chapter
```sql
INSERT INTO chapters VALUES (NULL, 1, 1, 'Chapter 1', 'ch1.pdf', datetime('now'));
```

---

## 🎓 Key Concepts

| Concept | Explanation |
|---------|-------------|
| **book_type** | Column that identifies if record is 'book' or 'manga' |
| **Chapter Number** | Sequential identifier for chapters (1, 2, 3...) |
| **UNIQUE Constraint** | Prevents duplicate (manga_id, chapter_num) pairs |
| **Foreign Key** | Links chapters to their manga parent record |
| **Secure Filename** | Sanitizes filenames to prevent security issues |

---

**Last Updated**: December 2024  
**Version**: 1.0  
**Status**: Production Ready ✅
