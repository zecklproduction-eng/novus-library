# Modern Manga Reader - Complete Guide

## Overview
A completely redesigned manga reading interface with modern dark theme, cyan accents, and integrated AI features.

## Access the New Reader
- URL: `http://127.0.0.1:5000/manga/{manga_id}`
- Example: `http://127.0.0.1:5000/manga/6`
- Old URL still works: `http://127.0.0.1:5000/manga/read/{manga_id}`

## Interface Layout

### Top Bar
- **Chapter Display**: Shows current chapter number and title
- **AI INSIGHTS Button**: Opens AI analysis panel (cyan button)
- **Settings (⚙️)**: Opens reader settings modal
- **Report Issue (🚩)**: Submit issue reports for the manga
- **Menu (☰)**: Hamburger menu for mobile/tablet

### Main Content Area (Left)
- **Manga Pages Container**: Displays manga pages/images
- **Page Navigation**:
  - PREV button: Go to previous page
  - Progress Slider: Jump to specific page percentage
  - Page Counter: Shows "Page X/Y"
  - NEXT button: Go to next page (cyan)

### Right Sidebar
Contains three main sections:

#### 1. AI Chatbot Card
- **Tabs**: AI CHATBOT | AI TRANSLATE PANEL
- **Toggle Switch**: Enable/Disable AI Assistant
- Connected to translation and chatbot services

#### 2. AI Assistant Card
- **Smart Summary**: Auto-generated chapter summary with 3 key points
- **VIEW FULL ANALYSIS**: Button to see detailed AI analysis
- Shows chapter-specific insights

#### 3. Character Profiles Card
- **Character List**: Shows main characters
- **Info**: Character name, trait/role
- **Voice Actor Badge**: Indicates voice-acted characters
- **Show More**: Expand to see additional characters

## Settings Modal

Access by clicking the Settings (⚙️) button.

### Available Settings
1. **Reading Mode**
   - Single: One page at a time
   - Double: Two pages side-by-side
   - Vertical: Vertical scrolling
   - Horizontal: Horizontal scrolling

2. **Background**
   - Light: White background
   - Dark: Dark background
   - Sepia: Warm sepia tone

3. **Brightness**
   - Slider: 0-200% brightness control

4. **Font Size**
   - Small: Compact text
   - Medium: Default size
   - Large: Larger text

All settings are saved to browser localStorage and persist across sessions.

## Features

### Navigation
- **Chapter Selection**: Shown in the top bar chapter display
- **Page Navigation**: Use PREV/NEXT buttons or slider
- **Progress Tracking**: Slider shows current page position

### AI Integration
- **Smart Summaries**: Auto-generated chapter summaries
- **Character Information**: AI-powered character profiles
- **Translation Panel**: Integrated translation support
- **Chatbot**: Ask questions about the chapter/series

### Responsive Design
- **Desktop**: Full layout with all features
- **Tablet**: Sidebar may be reduced
- **Mobile**: Stack layout with optimized spacing

## Color Scheme
- **Background**: Dark navy (#1a1a2e)
- **Accent**: Cyan (#00d4ff)
- **Text**: Light gray (#e0e0e0)
- **Cards**: Semi-transparent dark blue (#0f3460)
- **Borders**: Cyan with glow effect

## Keyboard Shortcuts (Ready to add)
Can be implemented:
- `Left Arrow`: Previous page
- `Right Arrow`: Next page
- `Space`: Next page
- `Esc`: Close settings modal
- `S`: Open settings
- `R`: Report issue

## JavaScript Features

### Settings Persistence
```javascript
// Settings are stored in localStorage
localStorage.getItem('mangaReaderSettings')
// Returns: { readingMode, backgroundColor, brightness, fontSize, aiAssistantEnabled }
```

### Available Functions
- `previousPage()`: Navigate to previous page
- `nextPage()`: Navigate to next page
- `loadChapter(chapterId)`: Load specific chapter
- `previousChapter()`: Load previous chapter
- `nextChapter()`: Load next chapter
- `closeSettings()`: Close settings modal
- `saveSettings()`: Save current settings
- `loadSettings()`: Load saved settings

## API Endpoints Used

### Report Manga
```
POST /report_manga
{
  "manga_id": 6,
  "reason": "Issue description"
}
```

### AI Features (Ready to connect)
- `/ai_summary`: Generate summaries
- `/ai_translate`: Translate text
- `/ai_analysis`: Get chapter analysis
- `/character_profiles`: Fetch character info

## Customization Options

### Add More Characters
Edit the character profiles section in `templates/manga_reader_new.html` (around line 380)

### Modify Color Scheme
Update CSS variables at the top of the template (lines 6-50)

### Add More Settings
Add new setting items in the settings modal (around line 450)

## Browser Compatibility
- Chrome/Edge: Full support
- Firefox: Full support
- Safari: Full support (except some CSS animations)
- Mobile browsers: Responsive layout support

## Performance Notes
- Lightweight CSS and minimal JavaScript
- Settings stored in localStorage (no server calls)
- Images lazy-loaded when available
- Smooth transitions and animations
- Optimized for modern browsers

## Troubleshooting

### Settings not saving?
- Check if localStorage is enabled
- Clear browser cache and try again
- Check browser console for errors

### Pages not loading?
- Ensure chapters have pages/images in database
- Check file paths in static folder
- Verify manga_id is correct

### AI Features not working?
- Ensure backend endpoints are implemented
- Check API endpoints in app.py
- Verify user is logged in

## Future Enhancements
- [ ] Keyboard shortcuts
- [ ] Bookmarks/favorites
- [ ] Reading history
- [ ] Custom themes
- [ ] Social sharing
- [ ] Comments/discussion
- [ ] Reading progress sync
- [ ] Offline reading mode
