@echo off
REM Database Setup Script for Flask React App (Windows)
REM This script automatically sets up the database with all required tables

echo.
echo ================================================
echo  Flask React App - Database Setup (Windows)
echo ================================================
echo.

cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python and make sure it's in your PATH
    pause
    exit /b 1
)

REM Check if we're in the backend directory
if not exist "app_factory.py" (
    echo ERROR: This script must be run from the backend directory
    echo Current directory: %CD%
    echo Please navigate to: apps\backend
    pause
    exit /b 1
)

echo Running database setup...
echo.

python setup_database.py

if errorlevel 1 (
    echo.
    echo ERROR: Database setup failed!
    echo Please check the error messages above.
) else (
    echo.
    echo SUCCESS: Database setup completed!
    echo You can now start the application with: npm run dev
)

echo.
pause