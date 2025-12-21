# Manga Reader Settings Integration Plan

## Issues Found:
1. **Missing variable declarations**: `autoSpeed` and `autoLabel` referenced but not properly declared
2. **Incomplete HTML structure**: Some setting buttons are missing from the modal
3. **Broken event handlers**: Some setting controls have undefined elements
4. **Settings persistence**: Not all settings are properly saved/loaded from localStorage
5. **Function integration**: Settings changes not properly applied to the reader

## Plan to Fix Reader Settings:

### Step 1: Fix Variable Declarations and HTML Structure
- Add missing variable declarations for `autoSpeed` and `autoLabel`
- Complete the settings modal HTML structure
- Ensure all setting buttons have proper IDs and event handlers

### Step 2: Fix Reading Mode Settings
- Complete implementation of Single Page, Double Page, Continuous modes
- Fix Vertical Scroll, Horizontal Scroll, and Webtoon modes
- Ensure proper page display logic for each mode

### Step 3: Fix Background Color Settings
- Complete Light, Dark, Sepia background implementations
- Apply background colors to both image and PDF viewers
- Ensure text color contrasts properly

### Step 4: Fix Fit Mode Settings
- Complete Fit Width, Fit Height, Actual Size implementations
- Apply proper scaling to both images and PDF pages
- Handle responsive behavior

### Step 5: Fix Direction Settings
- Complete Left-to-Right and Right-to-Left implementations
- Apply direction changes to page containers
- Handle reading flow direction

### Step 6: Fix Auto-Scroll Settings
- Fix auto-scroll speed control
- Implement proper start/stop functionality
- Apply speed changes in real-time

### Step 7: Fix Rotation Settings
- Complete left, right, and reset rotation implementations
- Apply rotation to both images and PDF pages
- Handle cumulative rotation

### Step 8: Fix Header Sticky and Remember Progress
- Complete header sticky toggle functionality
- Fix progress saving and restoration
- Apply header positioning changes

### Step 9: Test All Settings Integration
- Test each setting individually
- Test combinations of settings
- Ensure settings persist across page reloads
- Verify settings apply correctly to both image and PDF readers

## Files to Edit:
- `templates/chapter_viewer.html` - Main fixes and improvements
- `static/css/style.css` - Additional CSS for settings (if needed)

## Expected Outcome:
- All reader settings work seamlessly
- Settings persist between sessions
- Proper integration with both image and PDF readers
- Responsive and intuitive user experience
