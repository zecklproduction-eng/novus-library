# Manga Reader Button Test Guide

## Overview
This guide verifies that all buttons in the manga reading interface are properly wired and functional.

## Server Status
- Start server: `python app.py`
- Server URL: `http://127.0.0.1:5000`

## Test Pages
1. **Series Reader**: `http://127.0.0.1:5000/manga_reader/6`
2. **Chapter Viewer**: `http://127.0.0.1:5000/chapter_viewer/6/1`

## Chapter Viewer Buttons (ID: 6, Chapter: 1)

### Top Bar
- **Back Arrow**: Returns to previous page ✅
- **Settings (⚙️)**: Opens settings modal ✅
- **Back to Series**: Navigation link ✅

### Reader Header
- **Previous Chapter (◀)**: Navigate to previous chapter ✅
- **Chapter Dropdown**: Select chapter by number ✅
- **Next Chapter (▶)**: Navigate to next chapter ✅

### Action Buttons
- **Settings (⚙️)**: Opens settings modal with reading mode, background color, fit mode, direction, rotation, auto-scroll options
- **Fullscreen (⛶)**: Toggles fullscreen mode
- **Open PDF (📄)**: Opens PDF in new window (if PDF available)
- **Zoom Out (-)**: Reduces zoom level
- **Reset Zoom (0)**: Resets zoom to 100%
- **Zoom In (+)**: Increases zoom level
- **Share (↗️)**: Shares URL or copies to clipboard

### Footer Controls
- **Previous Page (◀)**: Navigate to previous page
- **Page Progress Slider**: Drag to jump to specific page percentage
- **Next Page (▶)**: Navigate to next page
- **Page Counter**: Shows current page and total pages

## Settings Modal Options

### Reading Mode
- [ ] Single Page
- [ ] Double Page
- [ ] Continuous
- [ ] Vertical Scroll
- [ ] Horizontal Scroll
- [ ] Webtoon

### Background Color
- [ ] Light
- [ ] Dark
- [ ] Sepia

### Fit Mode (Image Pages Only)
- [ ] Width
- [ ] Height
- [ ] Actual Size

### Direction
- [ ] LTR (Left-to-Right)
- [ ] RTL (Right-to-Left)

### Advanced Options
- [ ] Auto-scroll toggle with speed slider
- [ ] Rotation buttons (↻ ↺)
- [ ] Header sticky toggle
- [ ] Remember progress checkbox

## Series Reader Buttons (ID: 6)

### Top Bar
- **Back Arrow**: Returns to previous page
- **Settings (⚙️)**: Opens series-level settings
- **Fullscreen (⛶)**: Fullscreen embed
- **Zoom Out (-)**: Series zoom out
- **Zoom In (+)**: Series zoom in
- **Open PDF (📄)**: Open PDF in new window
- **Share (↗️)**: Share series URL
- **Report (🚩)**: Report series

### Reader Main
- **Chapters List Toggle**: Show/hide chapters
- **Chapter Selection**: Click chapter to navigate

## Browser Console Checks
When opening either page, check browser DevTools (F12 → Console) for:

1. ✅ No JavaScript errors
2. ✅ DOMContentLoaded fires once (not multiple times)
3. ✅ Event listeners attached successfully
4. ✅ PDF.js loading logs (if chapter has PDF)
5. ✅ "Rendering chapter PDF via PDF.js" message (if applicable)
6. ✅ Setting initialization logs

## Expected Console Output Examples

For image-based chapters:
```
Setting groups found: 3
Reading mode buttons: 6
BG color buttons: 3
Remember checkbox: <checkbox>
Settings initialized: {...}
```

For PDF-based chapters:
```
Rendering chapter PDF via PDF.js http://127.0.0.1:5000/static/books/...
PDF loaded successfully
Page 1 rendered via PDF.js
Page 2 rendered via PDF.js
```

## Test Checklist

### Basic Navigation
- [ ] Previous/Next chapter buttons work
- [ ] Chapter dropdown works
- [ ] Page counter updates correctly
- [ ] Progress slider updates page view

### Settings Modal
- [ ] Modal opens on settings click
- [ ] Reading mode buttons toggle active state
- [ ] Background color buttons toggle active state
- [ ] Settings persist in localStorage

### Zoom Controls
- [ ] Zoom in increases image size
- [ ] Zoom out decreases image size
- [ ] Reset zoom returns to original size
- [ ] Ctrl+Scroll wheel zooms (if supported)

### Full Screen
- [ ] Fullscreen button enters fullscreen
- [ ] Escape key exits fullscreen
- [ ] ESC key works in fullscreen

### Sharing
- [ ] Share button opens share dialog or copies link
- [ ] Modal closes when clicking outside

### PDF Rendering (if applicable)
- [ ] PDF pages render as canvases
- [ ] First 2 pages render immediately
- [ ] Remaining pages lazy-load on scroll
- [ ] Page displays correctly at container width

### Reading Modes
- [ ] Single page: Shows one page per screen
- [ ] Double page: Shows two pages side-by-side
- [ ] Vertical scroll: Continuous vertical scroll
- [ ] Horizontal scroll: Horizontal scrolling
- [ ] Webtoon: Full-width scrolling

## Debugging Tips

### If buttons don't respond:
1. Check browser console for JavaScript errors
2. Verify DOMContentLoaded fires: `document.readyState`
3. Check if elements exist: `document.getElementById('btnFullscreen')`
4. Verify event listeners: Open DevTools → inspect element → event listeners tab

### If PDF doesn't render:
1. Check console for PDF.js logs
2. Verify PDF URL is correct: `document.getElementById('pdfViewer')?.src`
3. Check if PDF file exists: Navigate to `/static/books/{filename}`
4. Ensure PDF.js is loaded from CDN

### If settings don't persist:
1. Check localStorage: `localStorage.readingMode`, `localStorage.backgroundColor`, etc.
2. Verify localStorage is enabled
3. Check for console errors in settings handlers

## Performance Notes
- First page load may take 1-2 seconds for PDF rendering setup
- Lazy rendering means scrolling to later pages might have slight delay
- Image pages should load instantly (using <img> native lazy-load)
- Settings changes should apply immediately

## Fixed Issues
1. ✅ Duplicate DOMContentLoaded blocks removed
2. ✅ Helper functions (applyChapterFit, applyChapterDirection, applyRotation) moved to module scope
3. ✅ Event listener attachment consolidated into single DOMContentLoaded
4. ✅ Duplicate AI Summary handlers removed

## Next Steps
If issues persist after these fixes:
1. Check for any new JavaScript errors
2. Run integration tests: `python -m pytest tests/`
3. Review specific button handler logic in templates
4. Consider adding console.log statements to track execution flow
