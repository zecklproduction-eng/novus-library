# Activity Log Feature Guide

## Overview
The Activity Log feature tracks user reading activities including reading, starting, completing books, and AI summarizations. Users can view their recent activities through a beautiful modal interface in their profile dropdown.

## Features

### 1. **Modal Display**
- Beautiful cyan-themed modal matching NOVUS design
- Shows 5 most recent activities by default
- Displays activity icons, timestamps, and AI summary badges
- Reading progress level indicator with visual bar
- Smooth animations and hover effects

### 2. **Activity Types**
- **READ**: User opened/read a book
- **STARTED**: User began reading a new book  
- **COMPLETED**: User finished a book
- **SUMMARIZED**: Book was summarized with AI (includes badge)

### 3. **Time Formatting**
Relative time display:
- "Just now"
- "2 minutes ago"
- "5 hours ago"
- "3 days ago"
- "2 months ago"
- etc.

## Database Schema

### activity_log Table
```sql
CREATE TABLE activity_log (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    book_id INTEGER NOT NULL,
    activity_type TEXT NOT NULL,
    summary_generated INTEGER DEFAULT 0,
    timestamp TEXT DEFAULT (DATETIME('now')),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (book_id) REFERENCES books(id)
)
```

## API Endpoints

### GET /api/activity-log
Returns user's activity log entries as JSON

**Parameters:**
- `limit` (optional, default=5): Number of activities to return

**Response:**
```json
[
  {
    "type": "read",
    "title": "Chapter 35: The Shadow's Pursuit",
    "when": "Yesterday, 3:15 PM",
    "icon": "fa-book-open",
    "has_summary": true
  },
  ...
]
```

### POST /api/log-activity
Logs a new activity for the user

**Request Body:**
```json
{
  "book_id": 123,
  "type": "read",
  "has_summary": false
}
```

**Response:**
```json
{
  "success": true
}
```

## Integration Guide

### Logging Activities in Your Code

To log an activity when a user reads a book:

```javascript
// Log activity (can be called from any page)
fetch('/api/log-activity', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    book_id: 123,
    type: 'read',
    has_summary: false
  })
})
.then(response => response.json())
.then(data => console.log('Activity logged:', data));
```

### Triggering From Python (app.py)

When you want to log activities server-side:

```python
def log_user_activity(user_id, book_id, activity_type='read', summary_generated=False):
    """Helper function to log user activities"""
    conn = get_conn()
    c = conn.cursor()
    
    c.execute("""
        INSERT INTO activity_log (user_id, book_id, activity_type, summary_generated)
        VALUES (?, ?, ?, ?)
    """, (user_id, book_id, activity_type, 1 if summary_generated else 0))
    
    conn.commit()
    conn.close()

# Usage:
# log_user_activity(user_id=5, book_id=42, activity_type='completed', summary_generated=True)
```

## UI Components

### Modal Structure
- **Header**: "ACTIVITY LOG" title
- **Content**: List of activity items with icons and details
- **Reading Level**: Progress bar showing reading level
- **Footer**: "Close" and "VIEW FULL HISTORY" buttons

### Activity Item Layout
```
[Icon] Activity text "Book Title"     [Badge if applicable]
       Relative timestamp (e.g., "Yesterday, 3:15 PM")
```

### Styling Classes
- `.activity-log-modal`: Main modal container
- `.activity-log-dialog`: Modal dialog box
- `.activity-item`: Individual activity entry
- `.activity-icon`: Icon container with blue background
- `.activity-badge`: Green "AI Summarized" badge
- `.reading-level-bar`: Progress bar visualization

## Features To Implement

### Phase 1 (Current)
- ✅ Database table creation
- ✅ Modal UI with beautiful design
- ✅ Activity fetching and display
- ✅ Time formatting
- ✅ Reading level progress bar

### Phase 2 (Recommended)
- [ ] Log activities automatically when users:
  - Open book_detail page
  - Finish reading a chapter
  - Complete entire book
- [ ] Webhook integration to log when AI summaries are generated
- [ ] Email notifications for reading milestones
- [ ] Reading streak tracking
- [ ] Weekly activity summary

### Phase 3 (Advanced)
- [ ] Activity statistics and analytics
- [ ] Reading habit insights
- [ ] Social activity feed
- [ ] Achievement badges for reading milestones
- [ ] Activity export (CSV/PDF)

## Testing

### Manual Testing Checklist
- [ ] Click "Activity Log" in profile dropdown
- [ ] Modal appears with smooth animation
- [ ] Close button works
- [ ] "VIEW FULL HISTORY" button links to profile
- [ ] Activities display with correct icons
- [ ] Time formatting shows relative times
- [ ] AI Summarized badge appears when applicable
- [ ] Reading level bar displays correctly
- [ ] Modal responsiveness on mobile devices

### Database Testing
```sql
-- Check if table exists
SELECT name FROM sqlite_master WHERE type='table' AND name='activity_log';

-- Insert test activity
INSERT INTO activity_log (user_id, book_id, activity_type, summary_generated)
VALUES (1, 1, 'read', 1);

-- View activities
SELECT * FROM activity_log ORDER BY timestamp DESC LIMIT 5;
```

## Troubleshooting

### Modal Not Appearing
- Check browser console for JavaScript errors
- Verify `openActivityLogModal()` function exists in base.html
- Check if Flask is returning 401 (not logged in)

### Activities Not Showing
- Verify `activity_log` table exists in database
- Check if activities are being inserted correctly
- Ensure user_id matches session user
- Check network tab in browser dev tools for API response

### Styling Issues
- Verify CSS file is loaded (check Network tab)
- Clear browser cache (Ctrl+Shift+Del)
- Check for CSS conflicts with other styles

## Performance Notes

- Activity log queries are optimized with LIMIT clause
- Timestamps stored as ISO format for consistency
- Consider adding indexes on `user_id` and `timestamp` if table grows large:
  ```sql
  CREATE INDEX idx_activity_user_time ON activity_log(user_id, timestamp DESC);
  ```

## Future Enhancements

1. **Activity Filtering**: Filter by activity type (all, reading, completed, etc.)
2. **Date Range**: Show activities from specific date ranges
3. **Export**: Download activity history as CSV
4. **Analytics**: Show reading statistics and trends
5. **Notifications**: Real-time activity notifications
6. **Badges**: Unlock badges for reading achievements
7. **Social**: Share reading activities with other users
