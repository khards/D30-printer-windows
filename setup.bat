@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo Python was not found.
    echo Install it from https://www.python.org/downloads/
    echo On the first install screen, tick "Add python.exe to PATH", then run this file again.
    pause
    exit /b 1
)

echo Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo Failed to create the virtual environment. See the error above.
    pause
    exit /b 1
)

echo Installing dependencies...
venv\Scripts\pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install dependencies. See the error above.
    pause
    exit /b 1
)

echo Registering the server to start when you sign in...
venv\Scripts\python.exe startup.py install
if errorlevel 1 (
    echo Failed to register startup. See the error above.
    pause
    exit /b 1
)

echo.
echo Setup complete. The server will start when you sign in.
echo Double-click start_server.bat to start printing now.
pause
