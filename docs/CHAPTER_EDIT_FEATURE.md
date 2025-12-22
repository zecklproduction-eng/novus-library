# Chapter Edit Feature

## Overview
Chapters are now fully editable! Users can re-upload PDF or image files for any chapter, and also delete chapters if needed.

## Features Added

### 1. **Edit Chapter** (`/manga/<manga_id>/chapter/<chapter_num>/edit`)
   - **GET Request**: Display the edit chapter form with current chapter information
   - **POST Request**: Update chapter content with new PDF or image files
   - **Features**:
     - Update chapter title
     - Re-upload images (replaces all existing pages)
     - Re-upload PDF (extracts pages and replaces content)
     - Clear visual display of current chapter info (chapter number, title, page count)

### 2. **Delete Chapter** (`/manga/<manga_id>/chapter/<chapter_num>/delete`)
   - Permanently delete a chapter from the system
   - Removes chapter directory and all associated files
   - Confirmation dialog prevents accidental deletion
   - Redirects back to chapter management page

### 3. **Updated Chapter List UI**
   - Each chapter in the "Existing Chapters" list now has an "EDIT" button
   - Click to open the edit page for that chapter
   - Visual feedback with hover effects

## User Interface

### Edit Chapter Page
Located at: `templates/edit_chapter.html`

**Layout:**
- Back button to return to chapters list
- Current chapter information display
  - Chapter number
  - Chapter title
  - Page count
- Upload section with:
  - Optional title update field
  - Format selection (Images or PDF)
  - Drag-and-drop file upload
  - File preview
  - Save Changes button
  - Delete button (with confirmation)

**Features:**
- Same modern design as the main upload chapter page
- Real-time file preview
- File count display
- Drag-and-drop support for both images and PDFs
- Clear error/success messages

### Chapter List (Upload Page)
Located at: `templates/upload_chapter.html`

**Changes:**
- Added EDIT button to each chapter card
- Button styling matches the application theme
- Smooth hover transitions
- Link opens edit chapter page

## Backend Routes

### 1. `edit_chapter(manga_id, chapter_num)`
**Route:** `@app.route("/manga/<int:manga_id>/chapter/<int:chapter_num>/edit", methods=["GET", "POST"])`

**Functionality:**
- **GET**: Retrieves chapter data and displays edit form
- **POST**: Processes file uploads and updates database
  - Validates files (PDF or images)
  - Clears old chapter directory
  - Saves new files
  - Updates database records
  - Returns success/error messages

### 2. `delete_chapter_by_num(manga_id, chapter_num)`
**Route:** `@app.route("/manga/<int:manga_id>/chapter/<int:chapter_num>/delete", methods=["GET"])`

**Functionality:**
- Retrieves chapter information
- Deletes chapter directory and all files
- Removes chapter record from database
- Confirms deletion and redirects

## File Structure Changes

```
templates/
├── upload_chapter.html (modified - added edit buttons)
└── edit_chapter.html (new - edit/delete page)

app.py (modified)
├── edit_chapter() - new function
└── delete_chapter_by_num() - new function
```

## Database Interactions

**Table: chapters**

Operations performed:
1. **Read**: Fetch chapter data for display
2. **Update**: Modify chapter title and content (pdf_filename, page_count)
3. **Delete**: Remove chapter record

**Example Update:**
```sql
UPDATE chapters
SET title = ?, pdf_filename = ?, page_count = ?
WHERE id = ?
```

## File Management

### Directory Handling
- Chapter directories: `static/manga/manga_{manga_id}_ch{chapter_num}/`
- When editing: Old directory is removed, new one created
- Files are re-numbered sequentially: `page_001.png`, `page_002.png`, etc.

### Supported Formats
- **Images**: JPG, PNG (max 5MB each)
- **PDF**: PDF files (max 50MB)
  - Converted to PNG images when extracted
  - Falls back to storing PDF filename if extraction unavailable

## User Experience Flow

1. User navigates to "Upload Chapter" page for a manga
2. Sees list of existing chapters with EDIT buttons
3. Clicks EDIT for desired chapter
4. Edit page loads with current chapter info
5. User can:
   - Update chapter title
   - Upload new images or PDF
   - Save changes or delete chapter
6. Page redirects back to chapter list with confirmation message

## Error Handling

- **File Not Found**: User is redirected with error message
- **Invalid File Format**: Flash message explaining allowed formats
- **No Files Uploaded**: Option to save title-only changes
- **Directory Deletion**: Safely removes directory with `shutil.rmtree()`

## Security Considerations

- Files are validated before processing
- Directory paths use `os.path.join()` for safety
- File names are sanitized with `secure_filename()`
- Confirmation dialog prevents accidental deletion

## Example Usage

### Edit Images for Chapter 1
```
1. Go to /manga/upload/6
2. Find Chapter 1 card
3. Click EDIT button
4. Upload new image files
5. Click SAVE CHANGES
6. Confirmation message appears
```

### Edit PDF for Chapter 2
```
1. Go to /manga/upload/6
2. Find Chapter 2 card
3. Click EDIT button
4. Select PDF format
5. Upload new PDF
6. Click SAVE CHANGES
7. PDF is extracted and pages are updated
```

### Delete a Chapter
```
1. Go to /manga/upload/6
2. Find chapter to delete
3. Click EDIT button
4. Click DELETE button at bottom
5. Confirm deletion in popup
6. Chapter is removed from system
```

## Future Enhancements (Optional)

- Bulk edit multiple chapters
- Reorder chapters
- Create chapter versions/history
- Chapter-specific settings (zoom, background)
- Permission-based editing (only author/admin)
- Archive chapters instead of deleting
