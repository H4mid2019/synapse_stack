"""
Simple startup script for development with text extraction
"""

import os
import subprocess
import sys
import time


def check_and_setup_database():
    """Check database and run setup if needed"""
    print("Checking database...")

    # Try to run database setup (it will skip if already set up)
    try:
        result = subprocess.run(
            [sys.executable, "setup_database.py"], capture_output=True, text=True, check=False, timeout=60
        )

        if result.returncode == 0:
            print("Database setup verified")
        else:
            print("Database setup failed:", result.stderr)
            return False

    except subprocess.TimeoutExpired:
        print("Database setup timed out")
        return False
    except Exception as e:
        print(f"Error checking database: {e}")
        return False

    # Run content migration
    try:
        result = subprocess.run(
            [sys.executable, "migrate_content_fields.py"], capture_output=True, text=True, check=False, timeout=30
        )

        if result.returncode == 0:
            print("Content fields migration completed")
        else:
            print("Migration output:", result.stdout)

    except Exception as e:
        print(f"Migration error: {e}")

    return True


def main():
    """Start all services"""
    print("Starting Flask React App with Text Extraction...")
    print("=" * 50)

    # Check database first
    if not check_and_setup_database():
        print("Database setup failed. Exiting.")
        sys.exit(1)

    # Start the full service stack
    try:
        subprocess.run([sys.executable, "start_local_with_extractor.py"], check=True)
    except KeyboardInterrupt:
        print("\nShutting down...")
    except subprocess.CalledProcessError as e:
        print(f"Error starting services: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
