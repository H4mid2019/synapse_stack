@echo off
setlocal enabledelayedexpansion

echo ========================================
echo Linting and Formatting
echo ========================================
echo.

set ERROR_OCCURRED=0

echo [1/5] Detecting changed Python files...
cd apps\backend
for /f "delims=" %%i in ('git diff --name-only --diff-filter=ACMR HEAD "*.py" 2^>nul') do (
    set "FILE_PATH=%%i"
    if "!FILE_PATH:~0,12!"=="apps/backend" (
        set "REL_PATH=!FILE_PATH:apps/backend/=!"
        set "PY_FILES=!PY_FILES! !REL_PATH!"
    )
)
for /f "delims=" %%i in ('git diff --cached --name-only --diff-filter=ACMR "*.py" 2^>nul') do (
    set "FILE_PATH=%%i"
    if "!FILE_PATH:~0,12!"=="apps/backend" (
        set "REL_PATH=!FILE_PATH:apps/backend/=!"
        set "PY_FILES=!PY_FILES! !REL_PATH!"
    )
)

if defined PY_FILES (
    echo Found changed Python files: %PY_FILES%
    echo.
    
    echo [2/5] Backend - Formatting with black...
    python -m black %PY_FILES%
    if %ERRORLEVEL% neq 0 (
        echo Backend black formatting failed
        set ERROR_OCCURRED=1
    ) else (
        echo Backend black formatting complete
    )
    echo.
    
    echo [3/5] Backend - Formatting with isort...
    python -m isort %PY_FILES%
    if %ERRORLEVEL% neq 0 (
        echo Backend isort formatting failed
        set ERROR_OCCURRED=1
    ) else (
        echo Backend isort formatting complete
    )
    echo.
    cd ..\..
) else (
    echo No changed Python files found in apps/backend
    echo [2/5] Backend - Skipped
    echo [3/5] Backend - Skipped
    echo.
    cd ..\..
)

echo [4/5] Frontend - Formatting (prettier)...
call npm run format
if %ERRORLEVEL% neq 0 (
    echo Frontend formatting failed
    set ERROR_OCCURRED=1
) else (
    echo Frontend formatting complete
)
echo.

echo [5/5] Frontend - Linting and fixing (eslint --fix)...
cd apps\frontend
call npx eslint . --fix
if %ERRORLEVEL% neq 0 (
    echo Frontend linting failed
    set ERROR_OCCURRED=1
) else (
    echo Frontend linting complete
)
echo.

cd ..\..

echo ========================================
if %ERROR_OCCURRED% equ 0 (
    echo All checks passed
    echo ========================================
    exit /b 0
) else (
    echo Some checks failed
    echo ========================================
    exit /b 1
)
