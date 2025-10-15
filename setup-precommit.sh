#!/bin/bash
# Setup script for native git pre-commit hooks

echo "Setting up native git pre-commit hooks..."

# Create the pre-commit hook file
echo "Creating .git/hooks/pre-commit..."

cat > .git/hooks/pre-commit << 'EOF'
#!/bin/sh
# Native git pre-commit hook
# Runs linting, formatting, and tests before commit

echo "Running pre-commit checks..."

# Get list of staged files
STAGED_PY_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$')
STAGED_TS_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '\.\(ts\|tsx\|js\|jsx\)$')

# Check if there are Python files to check
if [ -n "$STAGED_PY_FILES" ]; then
    echo "Checking Python files..."
    
    cd apps/backend
    
    # Run flake8 on Python files
    echo "Running flake8..."
    python -m flake8 $STAGED_PY_FILES --max-line-length=120 --extend-ignore=E203,W503
    if [ $? -ne 0 ]; then
        echo "flake8 failed. Fix the issues and try again."
        exit 1
    fi
    
    # Run black check on Python files  
    echo "Checking black formatting..."
    python -m black --check $STAGED_PY_FILES
    if [ $? -ne 0 ]; then
        echo "Black formatting issues found. Run 'python -m black .' to fix."
        exit 1
    fi
    
    # Run isort check on Python files
    echo "Checking import sorting..."
    python -m isort --check $STAGED_PY_FILES
    if [ $? -ne 0 ]; then
        echo "Import sorting issues found. Run 'python -m isort .' to fix."
        exit 1
    fi
    
    # Run tests
    echo "Running Python tests..."
    python -m pytest tests/ -v
    if [ $? -ne 0 ]; then
        echo "Tests failed. Fix the issues and try again."
        exit 1
    fi
    
    cd ../..
fi

# Check TypeScript/JavaScript files
if [ -n "$STAGED_TS_FILES" ]; then
    echo "Checking TypeScript/JavaScript files..."
    
    cd apps/frontend
    
    # Run ESLint
    echo "Running ESLint..."
    npx eslint $STAGED_TS_FILES
    if [ $? -ne 0 ]; then
        echo "ESLint failed. Fix the issues and try again."
        exit 1
    fi
    
    # Run Prettier check
    echo "Checking Prettier formatting..."
    npx prettier --check $STAGED_TS_FILES
    if [ $? -ne 0 ]; then
        echo "Prettier formatting issues found. Run 'npx prettier --write .' to fix."
        exit 1
    fi
    
    # Run TypeScript type check
    echo "Running TypeScript type check..."
    npm run type-check
    if [ $? -ne 0 ]; then
        echo "TypeScript type check failed. Fix the issues and try again."
        exit 1
    fi
    
    cd ../..
fi

echo "All pre-commit checks passed!"
exit 0
EOF

# Make the hook executable
chmod +x .git/hooks/pre-commit

echo "Pre-commit hook created successfully!"

echo ""
echo "Testing the hook..."
echo "You can test it by running: git commit (it will run automatically)"

echo ""
echo "Pre-commit hooks setup complete!"
echo ""
echo "Usage:"
echo "- Hook will run automatically before each commit"
echo "- To skip hook: git commit --no-verify" 
echo "- Hook checks only staged files, not all files"