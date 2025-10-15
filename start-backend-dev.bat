@echo off
echo Starting Backend Services with Text Extractor...
echo.

REM Activate virtual environment if it exists
if exist apps\backend\.venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call apps\backend\.venv\Scripts\activate.bat
)

REM Set development mode
set FLASK_ENV=development
set TEST_MODE=false

echo Starting all backend services...
cd apps\backend
python start_local_with_extractor.py

pause