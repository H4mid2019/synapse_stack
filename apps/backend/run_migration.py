#!/usr/bin/env python3
"""
Simple migration runner for production
"""
from flask_migrate import upgrade
from app_factory import create_app

# Create the operations app (has full database access)
app = create_app('operations')

with app.app_context():
    print("Running database migrations...")
    try:
        upgrade()
        print("✅ Migrations completed successfully!")
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise
