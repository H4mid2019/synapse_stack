@echo off
REM Main Database Setup Script (Windows)
REM Run this from anywhere in the project to set up the database

echo.
echo ================================================
echo  Flask React App - Database Setup
echo ================================================
echo.

REM Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"
set "BACKEND_DIR=%SCRIPT_DIR%apps\backend"

REM Check if backend directory exists
if not exist "%BACKEND_DIR%" (
    echo ERROR: Backend directory not found at: %BACKEND_DIR%
    echo Make sure you're running this script from the project root directory.
    pause
    exit /b 1
)

echo Navigating to backend directory...
cd /d "%BACKEND_DIR%"

echo Running database setup from: %CD%
echo.

REM Run the backend setup script
call setup_database.bat

REM Return to original directory
cd /d "%SCRIPT_DIR%"
