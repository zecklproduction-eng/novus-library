@echo off
echo ================================
echo   Starting NOVUS E-LIBRARY...
echo ================================

REM Move to the project directory
cd /d "%~dp0"

REM Configure AI API Key
set GEMINI_API_KEY=AIzaSyBlgCkZOoGRFX38rQSvCICGwsL-Duy6ydQ

REM Activate virtual environment
if exist .venv (
    echo Activating virtual environment...
    call .venv\Scripts\activate
) else (
    echo Virtual environment not found!
    echo Creating new one...
    python -m venv .venv
    call .venv\Scripts\activate
    pip install -r requirements.txt
)

echo Running Flask app...
python app.py

echo.
echo Application stopped.
pause
echo.