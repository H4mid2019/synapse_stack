@echo off
echo Starting Full Development Environment...
echo.

REM Activate virtual environment if it exists
if exist apps\backend\.venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call apps\backend\.venv\Scripts\activate.bat
)

echo.
echo This will start:
echo - Backend services (proxy, read, write, operations)
echo - Text extraction service
echo - Frontend React app
echo.
echo Press Ctrl+C to stop all services
echo.

REM Start backend services in a new window
start "Backend Services" cmd /k "cd /d %CD%\apps\backend && python start_local_with_extractor.py"

REM Wait a moment for backend to start
timeout /t 5 /nobreak > nul

REM Start frontend in a new window
start "Frontend" cmd /k "cd /d %CD%\apps\frontend && npm run dev"

echo.
echo Services starting in separate windows...
echo Backend: http://localhost:5000
echo Frontend: http://localhost:3000  
echo Text Extractor: http://localhost:6004
echo.
echo Press any key to exit this launcher...
pause > nul