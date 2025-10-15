@echo off
echo Setting up database for Flask React App...
echo =========================================

cd /d "%~dp0apps\backend"

echo Checking Python environment...
python --version
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python and add it to PATH.
    pause
    exit /b 1
)

echo.
echo Running database setup...
python setup_database.py

if errorlevel 1 (
    echo.
    echo ERROR: Database setup failed. Check the logs above.
    pause
    exit /b 1
) else (
    echo.
    echo SUCCESS: Database setup completed!
    echo You can now run 'npm run dev' to start the application.
)

pause