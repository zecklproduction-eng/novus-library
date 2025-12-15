@echo off
REM Run the repository test runner using the virtualenv python
cd /d %~dp0
set PYTHONPATH=%CD%
call venv\Scripts\python.exe tests\run_verbose.py
pause
