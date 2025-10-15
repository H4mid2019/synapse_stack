@echo off
REM Setup script for native git pre-commit hooks on Windows

echo Setting up native git pre-commit hooks...

REM Create the pre-commit hook file
echo Creating .git\hooks\pre-commit...

(
echo #!/bin/sh
echo # Native git pre-commit hook
echo # Runs linting, formatting, and tests before commit
echo.
echo echo "Running pre-commit checks..."
echo.
echo # Get list of staged files
echo STAGED_PY_FILES=^$(git diff --cached --name-only --diff-filter=ACM ^| grep '\.py$'^)
echo STAGED_TS_FILES=^$(git diff --cached --name-only --diff-filter=ACM ^| grep '\.\(ts\^|tsx\^|js\^|jsx\^)$'^)
echo.
echo # Check if there are Python files to check
echo if [ -n "$STAGED_PY_FILES" ]; then
echo     echo "Checking Python files..."
echo     
echo     # Run flake8 on Python files
echo     cd apps/backend
echo     echo "Running flake8..."
echo     python -m flake8 $STAGED_PY_FILES --max-line-length=120 --extend-ignore=E203,W503
echo     if [ $? -ne 0 ]; then
echo         echo "flake8 failed. Fix the issues and try again."
echo         exit 1
echo     fi
echo     
echo     # Run black check on Python files  
echo     echo "Checking black formatting..."
echo     python -m black --check $STAGED_PY_FILES
echo     if [ $? -ne 0 ]; then
echo         echo "Black formatting issues found. Run 'python -m black .' to fix."
echo         exit 1
echo     fi
echo     
echo     # Run isort check on Python files
echo     echo "Checking import sorting..."
echo     python -m isort --check $STAGED_PY_FILES
echo     if [ $? -ne 0 ]; then
echo         echo "Import sorting issues found. Run 'python -m isort .' to fix."
echo         exit 1
echo     fi
echo     
echo     # Run tests
echo     echo "Running Python tests..."
echo     python -m pytest tests/ -v
echo     if [ $? -ne 0 ]; then
echo         echo "Tests failed. Fix the issues and try again."
echo         exit 1
echo     fi
echo     
echo     cd ../..
echo fi
echo.
echo # Check TypeScript/JavaScript files
echo if [ -n "$STAGED_TS_FILES" ]; then
echo     echo "Checking TypeScript/JavaScript files..."
echo     
echo     cd apps/frontend
echo     
echo     # Run ESLint
echo     echo "Running ESLint..."
echo     npx eslint $STAGED_TS_FILES
echo     if [ $? -ne 0 ]; then
echo         echo "ESLint failed. Fix the issues and try again."
echo         exit 1
echo     fi
echo     
echo     # Run Prettier check
echo     echo "Checking Prettier formatting..."
echo     npx prettier --check $STAGED_TS_FILES
echo     if [ $? -ne 0 ]; then
echo         echo "Prettier formatting issues found. Run 'npx prettier --write .' to fix."
echo         exit 1
echo     fi
echo     
echo     # Run TypeScript type check
echo     echo "Running TypeScript type check..."
echo     npm run type-check
echo     if [ $? -ne 0 ]; then
echo         echo "TypeScript type check failed. Fix the issues and try again."
echo         exit 1
echo     fi
echo     
echo     cd ../..
echo fi
echo.
echo echo "All pre-commit checks passed!"
echo exit 0
) > .git\hooks\pre-commit

REM Make the hook executable (Windows doesn't need this, but good practice)
echo Pre-commit hook created successfully!

echo.
echo Testing the hook...
echo You can test it by running: git commit (it will run automatically)

echo.
echo Pre-commit hooks setup complete!
echo.
echo Usage:
echo - Hook will run automatically before each commit
echo - To skip hook: git commit --no-verify
echo - Hook checks only staged files, not all files
pause