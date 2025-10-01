@echo off
REM WiRiP Blog Startup Script for Windows
REM This script helps you start the blog in development mode

echo 🎵 Starting WiRiP Blog...

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo Creating .env file from template...
    copy .env.example .env
    echo Please update the .env file with your configuration
)

REM Initialize database if it doesn't exist
if not exist "wirip.db" (
    echo Initializing database...
    python -c "from app import app, db, init_db; init_db(); print('Database initialized successfully!')"
)

echo ✅ Setup complete!
echo.
echo 📋 Quick Start:
echo    🌐 The blog will be available at: http://localhost:5000
echo    👤 Default admin login: admin / admin123
echo    ⚠️  Change the admin password after first login!
echo.
echo Starting the development server...

REM Start the application
python app.py

pause