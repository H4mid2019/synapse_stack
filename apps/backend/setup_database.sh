#!/bin/bash
# Database Setup Script for Flask React App (Linux/Mac)
# This script automatically sets up the database with all required tables

echo ""
echo "================================================"
echo " Flask React App - Database Setup (Linux/Mac)"
echo "================================================"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "ERROR: Python is not installed or not in PATH"
        echo "Please install Python 3"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

# Check if we're in the backend directory
if [ ! -f "app_factory.py" ]; then
    echo "ERROR: This script must be run from the backend directory"
    echo "Current directory: $(pwd)"
    echo "Please navigate to: apps/backend"
    exit 1
fi

echo "Using Python: $PYTHON_CMD"
echo "Running database setup..."
echo ""

$PYTHON_CMD setup_database.py

if [ $? -eq 0 ]; then
    echo ""
    echo "SUCCESS: Database setup completed!"
    echo "You can now start the application with: npm run dev"
else
    echo ""
    echo "ERROR: Database setup failed!"
    echo "Please check the error messages above."
    exit 1
fi

echo ""
