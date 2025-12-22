# Character Integration Guide

## Feature Overview

Characters added via **Add Character Info** in the manga editing page now automatically appear in the **Character Profiles** section of the manga reading page.

## How It Works

### User Workflow

#### 1. **Add Characters (Edit Manga Page)**
- Navigate to manga editing page: `/manga/edit/<manga_id>`
- Scroll to **"Add Character Info"** section
- Fill in character details:
  - **Character Name** (required) - e.g., "Tanjiro Kamado"
  - **Role** (optional) - e.g., "Protagonist", "Antagonist"
  - **Description** (optional) - Brief character background
  - **Character Photo** (optional) - Avatar image
- Click **"Add Character"** button
- Character is saved to database and appears in characters list

#### 2. **View Characters (Manga Reader)**
- Navigate to manga reader: `/manga/read/<manga_id>`
- Look at the **right sidebar** in the **Character Profiles** card
- All added characters automatically display with:
  - Avatar (if uploaded) or initial badge
  - Character name
  - Role/title
  - Description snippet (first 60 characters)
- If more than 3 characters exist, click **"↓ Show more"** to expand the list

### Backend Integration

**API Endpoint:**
```
GET /api/manga/<manga_id>/characters
```

**Response Format:**
```json
[
  {
    "id": 1,
    "name": "Tanjiro Kamado",
    "role": "Protagonist",
    "description": "A kind-hearted demon slayer...",
    "avatar_url": "/static/covers/char_image.jpg"
  },
  ...
]
```

**Authentication:** Requires login (session validation)

### Frontend Implementation

**HTML Structure (Manga Reader):**
```html
<div class="character-profiles" id="characterProfilesContainer">
  <!-- Characters loaded dynamically here -->
</div>
```

**JavaScript Function:**
```javascript
async function loadCharacterProfiles() {
  // Fetches characters from API
  // Renders character cards with avatars and info
  // Shows "Show more" button if >3 characters
}
```

## File Changes

### 1. **templates/manga_reader_new.html**

**Changes Made:**
- Replaced hardcoded character placeholders with dynamic loading container
- Added ID `characterProfilesContainer` for JavaScript targeting
- Added `loadCharacterProfiles()` function to fetch from database
- Added `toggleCharacterList()` to show/hide additional characters
- Added `escapeHtml()` for XSS protection

**Key Code Sections:**
```javascript
// Container for dynamic character loading
<div class="character-profiles" id="characterProfilesContainer">
  <!-- Characters will be loaded dynamically -->
</div>

// Function to load characters from API
async function loadCharacterProfiles() {
  const response = await fetch(`/api/manga/${mangaId}/characters`);
  const characters = await response.json();
  // Render character cards...
}

// Load on page initialization
loadCharacterProfiles();
```

### 2. **app.py** (No changes needed)

Existing endpoints already support character retrieval:
- `GET /api/manga/<manga_id>/characters` - List all characters
- `POST /api/manga/<manga_id>/characters` - Add new character
- `PUT /api/manga/character/<character_id>` - Update character
- `DELETE /api/manga/character/<character_id>` - Delete character

### 3. **templates/edit_book.html** (No changes needed)

Existing character management functionality:
- Add character form
- Character list display
- Edit character modal
- Delete character confirmation

## Feature Details

### Character Display

**First 3 Characters** - Always visible:
- Character avatar (or initial badge)
- Character name
- Character role
- Description snippet (truncated at 60 chars)

**Additional Characters** - Collapsible:
- "↓ Show 2 more" button appears if >3 characters
- Clicking expands to show remaining characters
- Button changes to "↑ Hide" when expanded

### Avatar Handling

**If Avatar URL exists:**
- Display character's uploaded image
- Circular crop with proper sizing
- Fallback styling for failed image loads

**If No Avatar:**
- Show gradient badge with character's first letter
- Gradient: `linear-gradient(135deg, #667eea, #00d4ff)`
- White text, centered, bold font

### XSS Protection

All character data is HTML-escaped before rendering:
```javascript
function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;  // Safe text content
  return div.innerHTML;
}
```

## Error Handling

**No Characters Added:**
```
"No characters added yet"
```

**API Error:**
```
"Error loading characters"
```

**Loading State:**
```
"Loading characters..."
```

## User Experience

### Visual Design

**Character Card Styling:**
- Responsive flexbox layout
- Avatar thumbnail with border-radius
- Character info in column layout
- Hover effects for better interactivity

**Colors:**
- Primary accent: `#00d4ff` (cyan)
- Text: `#000` (dark)
- Secondary text: `#999` (muted)
- Gradient: Purple to cyan (`#667eea` to `#00d4ff`)

### Responsive Design

**Desktop (>992px):**
- Character profiles in right sidebar
- Fixed width, scrollable if needed
- Show/hide with smooth transitions

**Tablet & Mobile:**
- Character section may be repositioned based on layout
- Touch-friendly expand/collapse buttons
- Mobile-optimized avatar sizes

## Testing Checklist

- [ ] Add a character via manga edit page
- [ ] Character appears in manga reader's Character Profiles section
- [ ] Character avatar displays correctly (or initial badge if no image)
- [ ] Character name, role, and description display
- [ ] "Show more" button appears when >3 characters exist
- [ ] Clicking "Show more" expands to show all characters
- [ ] Clicking "Hide" collapses extra characters
- [ ] API returns character data in correct JSON format
- [ ] Multiple characters display in order
- [ ] Character descriptions are truncated at 60 characters
- [ ] XSS protection works (special characters escaped)
- [ ] Page handles zero characters gracefully
- [ ] Character updates immediately after adding in edit page

## API Reference

### Get Characters
```
Method: GET
URL: /api/manga/<manga_id>/characters
Authentication: Required (session)
Status Codes:
  - 200: Success, returns array of characters
  - 401: Login required
  - 404: Manga not found
```

### Add Character
```
Method: POST
URL: /api/manga/<manga_id>/characters
Content-Type: multipart/form-data
Fields:
  - name (required): string
  - role (optional): string
  - description (optional): string
  - avatar (optional): file (image)
Authentication: Required
Status Codes:
  - 201: Created successfully
  - 400: Invalid input
  - 403: Permission denied
```

### Update Character
```
Method: PUT
URL: /api/manga/character/<character_id>
Content-Type: multipart/form-data
Fields: Same as POST
Status Codes:
  - 200: Updated successfully
  - 400: Invalid input
  - 403: Permission denied
  - 404: Character not found
```

### Delete Character
```
Method: DELETE
URL: /api/manga/character/<character_id>
Authentication: Required
Status Codes:
  - 204: Deleted successfully
  - 403: Permission denied
  - 404: Character not found
```

## Browser Compatibility

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

All modern browsers with:
- ES6 Promise support
- Fetch API
- CSS Flexbox
- DOM manipulation

## Performance Notes

**Character Loading:**
- Asynchronous API call (non-blocking)
- Lightweight JSON response
- Cached in browser memory

**Rendering:**
- Efficient DOM manipulation
- No unnecessary re-renders
- CSS transitions for expand/collapse

## Future Enhancement Ideas

1. **Character Search** - Filter characters by name or role
2. **Character Sorting** - Order by role, name, or custom
3. **Rich Descriptions** - Support markdown or HTML in descriptions
4. **Voice Acting Info** - Add voice actor details
5. **Character Relationships** - Show connections between characters
6. **Character Timeline** - Track character appearances in chapters
7. **Analytics** - Track which characters are most viewed

## Troubleshooting

**Characters not showing up?**

1. Check browser console for JavaScript errors
2. Verify characters were added via edit page
3. Confirm API endpoint returns data:
   ```
   GET http://127.0.0.1:5000/api/manga/<id>/characters
   ```
4. Clear browser cache and refresh
5. Check network tab to see if fetch request succeeds

**Avatar images not displaying?**

1. Verify image file was uploaded successfully
2. Check if image path is correct in database
3. Ensure file exists in `/static/covers/` directory
4. Try clearing browser cache
5. Check for CORS issues in console

**Show more button not working?**

1. Check if more than 3 characters exist
2. Verify JavaScript `toggleCharacterList()` is loaded
3. Check browser console for errors
4. Ensure DOM element `extraCharacters` exists

## Database Schema

**manga_characters Table:**
```sql
CREATE TABLE manga_characters (
    id          INTEGER PRIMARY KEY,
    manga_id    INTEGER NOT NULL,
    name        TEXT NOT NULL,
    description TEXT,
    role        TEXT,
    avatar_url  TEXT,
    created_at  TEXT DEFAULT (DATETIME('now')),
    FOREIGN KEY (manga_id) REFERENCES books(id)
);
```

## Summary

✅ **Feature Complete**

Characters added via the manga editing interface now automatically appear in the manga reader's Character Profiles section. The integration is:

- **Automatic** - No manual linking required
- **Real-time** - Changes reflect immediately after adding
- **Responsive** - Works on all device sizes
- **Secure** - XSS protection for user-generated content
- **Efficient** - Asynchronous loading, no page blocking
- **User-friendly** - Expandable list with "Show more" functionality
