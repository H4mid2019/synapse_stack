@echo off
echo Starting Flask React App with Text Extraction...
echo.

REM Activate virtual environment if it exists
if exist .venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
)

REM Run database migration for content extraction fields
echo Running database migration for content extraction...
python migrate_content_fields.py
if %ERRORLEVEL% NEQ 0 (
    echo Migration failed!
    pause
    exit /b 1
)

echo.
echo Migration completed successfully!
echo Starting all services with text extraction...
echo.

REM Start all services including text extractor
python start_local_with_extractor.py

pause