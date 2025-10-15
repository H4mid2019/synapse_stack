@echo off
echo Starting Text Extractor Service Only...
echo.

REM Activate virtual environment if it exists
if exist apps\backend\.venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call apps\backend\.venv\Scripts\activate.bat
)

REM Set development mode
set FLASK_ENV=development

echo Starting text extractor on port 6004...
cd apps\backend
python text_extractor.py

pause