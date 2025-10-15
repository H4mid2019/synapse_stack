#!/usr/bin/env python3
"""
Database Setup Script
Automatically sets up the database with all required tables and migrations
"""

import logging
import os
import sys

from flask_migrate import init, upgrade

from app_factory import create_app
from database import db

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def setup_database():
    """Setup database with all tables and migrations"""
    try:
        logger.info("Starting database setup...")

        # Create app instance
        app = create_app("operations")

        with app.app_context():
            logger.info("Testing database connection...")

            # Test connection
            try:
                db.session.execute(db.text("SELECT 1"))
                logger.info("✅ Database connection successful")
            except Exception as e:
                logger.error("❌ Database connection failed: %s", str(e))
                logger.error(
                    "Make sure your database server is running and DATABASE_URL is correct"
                )
                return False

            # Check if migrations directory exists
            migrations_dir = os.path.join(os.path.dirname(__file__), "migrations")
            if not os.path.exists(migrations_dir):
                logger.info("Initializing migration repository...")
                init()
                logger.info("✅ Migration repository initialized")

            # Create all tables
            logger.info("Creating database tables...")
            db.create_all()
            logger.info("✅ Database tables created")

            # Run migrations
            logger.info("Applying database migrations...")
            try:
                upgrade()
                logger.info("✅ Migrations applied successfully")
            except Exception as e:
                logger.warning("Migration warning (this might be normal): %s", str(e))

            # Verify tables exist
            logger.info("Verifying database tables...")
            result = db.session.execute(
                db.text(
                    "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
                )
            )
            tables = [row[0] for row in result]

            required_tables = ["users", "filesystem_items", "file_permissions"]
            missing_tables = [table for table in required_tables if table not in tables]

            if missing_tables:
                logger.error("❌ Missing tables: %s", missing_tables)
                return False

            logger.info("✅ All required tables verified: %s", required_tables)
            logger.info("📊 Database setup completed successfully!")

            return True

    except Exception as e:
        logger.error("❌ Database setup failed: %s", str(e))
        return False


def main():
    """Main entry point"""
    logger.info("🚀 Flask React App - Database Setup")
    logger.info("=" * 50)

    success = setup_database()

    if success:
        logger.info("🎉 Database is ready! You can now start the application.")
        sys.exit(0)
    else:
        logger.error("💥 Database setup failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
