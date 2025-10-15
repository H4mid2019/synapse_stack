@echo off
echo Starting Frontend Development Server...
echo.

REM Set development mode
set VITE_TEST_MODE=false
set NODE_ENV=development

echo Starting React development server...
cd apps\frontend
npm run dev

pause