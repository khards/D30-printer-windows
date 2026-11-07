@echo off
cd /d "%~dp0"
if not exist venv\Scripts\pythonw.exe (
    echo Setup hasn't been run yet. Double-click setup.bat first.
    pause
    exit /b 1
)

start "" venv\Scripts\pythonw.exe tray.py --open
