# Chapter Edit Feature - Quick Start Guide

## 🎯 What's New

Users can now **edit chapters** by uploading new PDF files or images, and **delete chapters** they no longer need.

## 📍 Where to Find It

1. Go to any manga's upload page: `/manga/upload/<manga_id>`
2. Look for the **"Existing Chapters"** section
3. Each chapter now has an **EDIT** button

```
┌─────────────────────────────────┐
│ Chapter 1                       │
│ Romance Dawn                    │
│ ┌──────────────────────────────┐│
│ │ [EDIT] button                ││
│ └──────────────────────────────┘│
└─────────────────────────────────┘
```

## 🔄 Editing a Chapter

### Step 1: Click EDIT Button
- Opens the edit chapter page
- Shows current chapter info:
  - Chapter number
  - Chapter title  
  - Current page count

### Step 2: Choose What to Update

**Option A: Update Title Only**
- Change the chapter title
- Click SAVE CHANGES
- No file upload needed

**Option B: Re-upload Images**
1. Select "Images (Multiple Pages)" format
2. Drag & drop or browse for image files (JPG, PNG)
3. See live preview of pages
4. Click SAVE CHANGES

**Option C: Re-upload PDF**
1. Select "PDF File" format
2. Drag & drop or browse for PDF file
3. PDF will be extracted to individual pages
4. Click SAVE CHANGES

### Step 3: Confirm

- Success message appears
- Redirected back to chapter list
- New content is live immediately

## 🗑️ Deleting a Chapter

1. Open chapter edit page
2. Click **DELETE** button (red button at bottom)
3. Confirm deletion in popup dialog
4. Chapter is permanently removed
   - All images/PDF deleted
   - Database record removed
5. Redirected back to chapter list

## 💡 Tips & Tricks

✅ **Best Practices:**
- Always upload images in correct order (page 1, 2, 3...)
- Use consistent image format (JPG or PNG)
- PDF extraction works best with clear, high-quality PDFs
- Title is optional (auto-generates "Chapter X" if blank)

⚠️ **Important:**
- Editing replaces ALL pages - old pages are deleted
- No undo for deletions - be careful!
- Requires same manga_id relationship
- Page numbering resets to 001, 002, etc.

📊 **File Limits:**
- Images: Max 5MB each
- PDFs: Max 50MB
- Supported image formats: JPG, PNG
- Supported PDF: Any standard PDF

## 🎨 UI Features

- **Drag & Drop**: Drop files directly on upload area
- **Live Preview**: See thumbnail of each page before saving
- **File Counter**: Shows how many pages/files selected
- **Format Toggle**: Switch between Images and PDF without reloading
- **Confirmation Dialog**: Prevents accidental deletion
- **Success Messages**: Clear feedback on what happened

## 🔗 Routes Reference

**Edit Chapter:**
```
GET/POST /manga/<manga_id>/chapter/<chapter_num>/edit
```

**Delete Chapter:**
```
GET /manga/<manga_id>/chapter/<chapter_num>/delete
```

**Example:**
```
Edit Chapter 2 of Manga 6:
/manga/6/chapter/2/edit

Delete Chapter 1 of Manga 6:
/manga/6/chapter/1/delete
```

## 🐛 Troubleshooting

**"Chapter not found" error**
- Make sure manga_id and chapter_num are correct
- Chapter may have been deleted

**"File upload failed"**
- Check file format (JPG, PNG for images; PDF for PDFs)
- Check file size (under 5MB for images, 50MB for PDF)
- Ensure proper file permissions

**"PDF extraction failed"**
- PDFs will still upload, but pages won't be extracted
- Install pdf2image for proper PDF support: `pip install pdf2image`

**Changes not showing in reader**
- Hard refresh browser (Ctrl+F5)
- Clear browser cache
- Check that page numbering is correct (page_001.png, etc.)

## 🔒 Permissions

- Currently, any logged-in user can edit chapters
- In the future: Only manga author/admin can edit
- Delete also follows same permission rules

## 📝 Example Workflow

**Scenario: Updating Chapter 1 with Better Image Quality**

1. Navigate to `/manga/upload/6` (Manga ID 6)
2. Find "Chapter 1: Romance Dawn" in Existing Chapters
3. Click the blue **[EDIT]** button
4. Edit page opens, showing:
   - Chapter: 1
   - Title: Romance Dawn
   - Pages: 3
5. Select "Images (Multiple Pages)" radio button
6. Drag 3 high-quality PNG files into upload area
7. See preview of all 3 pages in thumbnails
8. Click **SAVE CHANGES** button
9. Page redirects with success message
10. Old 3 pages are deleted, new ones are in place
11. Reader will show updated pages immediately

---

**Ready to try it?** Go to any manga's upload page and click EDIT on a chapter! 🚀
