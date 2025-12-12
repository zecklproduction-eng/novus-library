@echo off
echo ================================
echo   Starting NOVUS E-LIBRARY...
echo ================================

REM Move to the project directory
cd /d "%~dp0"

REM Activate virtual environment
if exist .venv (
    echo Activating virtual environment...
    call .venv\Scripts\activate
) else (
    echo Virtual environment not found!
    echo Creating new one...
    python -m venv .venv
    call .venv\Scripts\activate
    pip install flask
)

echo Running Flask app...
python app.py

echo.
echo Application stopped.
pause
