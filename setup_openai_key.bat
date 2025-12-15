@echo off
REM Set OpenAI API Key permanently for the project
REM Run this batch file once to configure

setx OPENAI_API_KEY "PASTE_YOUR_NEW_KEY_HERE"
setx USE_OPENAI true
setx OPENAI_MODEL gpt-4-turbo

echo.
echo =====================================================
echo ✓ OpenAI configuration saved!
echo =====================================================
echo.
echo Next steps:
echo 1. Replace PASTE_YOUR_NEW_KEY_HERE with your actual key
echo 2. Close all terminals and reopen them
echo 3. Run this batch file again
echo.
pause
