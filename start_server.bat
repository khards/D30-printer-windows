@echo off
if not exist venv\Scripts\python.exe (
    echo Setup hasn't been run yet. Double-click setup.bat first.
    pause
    exit /b 1
)

start "D30 Print Server" venv\Scripts\python.exe server.py
timeout /t 2 >nul
start "" http://localhost:8787/

echo The print server is running in the other window that just opened.
echo Your browser should have opened to the print page -- if not, go to:
echo   http://localhost:8787/
echo.
echo To stop the server, close the "D30 Print Server" window.
pause
