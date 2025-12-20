# Notification System Restructuring Plan

## Goal
Move the notification bell icon from its current position (separate element) into the profile dropdown menu as a functional "Notifications" option.

## Current State
- Notification bell is positioned as `.notification-container` before profile dropdown
- Has its own dropdown functionality with badge counter
- Profile dropdown already has "Notifications" link in ACCOUNT section
- Activity log system fully implemented

## Plan Steps

### 1. Remove Current Notification Bell
- Remove `.notification-container` from top navigation
- Remove associated CSS styles for the separate notification bell

### 2. Update Profile Dropdown "Notifications" Link
- Add notification badge counter to the existing "Notifications" link
- Make it clickable to toggle notification dropdown
- Style it as a proper notification option

### 3. Update CSS Styling
- Style the "Notifications" link with badge
- Ensure proper spacing and alignment in profile dropdown
- Update notification dropdown positioning if needed

### 4. Update JavaScript
- Modify notification toggle function to work with profile dropdown
- Ensure proper dropdown positioning and behavior
- Maintain all existing functionality (badge updates, mark as read, etc.)

### 5. Testing
- Verify notification dropdown appears correctly from profile menu
- Test badge counter updates
- Test mark as read functionality
- Test integration with activity log

## Expected Result
- Clean top navigation with only profile dropdown
- "Notifications" option in profile dropdown with badge counter
- Clicking it shows notification dropdown
- All existing functionality preserved
