"""Add content extraction fields to FileSystemItem

This script adds the new fields needed for text content extraction and search.
"""

import logging
import os
import sys

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import db
from models import FileSystemItem

logger = logging.getLogger(__name__)


def upgrade_database():
    """Add content extraction fields"""
    try:
        logger.info("Adding content extraction fields to filesystem_items table...")

        # Add new columns using raw SQL (SQLAlchemy 2.0 syntax)
        with db.engine.connect() as conn:
            conn.execute(
                db.text(
                    """
                ALTER TABLE filesystem_items 
                ADD COLUMN IF NOT EXISTS content_text TEXT,
                ADD COLUMN IF NOT EXISTS content_extracted BOOLEAN DEFAULT FALSE,
                ADD COLUMN IF NOT EXISTS extraction_error VARCHAR(500)
            """
                )
            )
            conn.commit()

        logger.info("Successfully added content extraction fields")
        return True

    except Exception as e:
        logger.error("Failed to add content extraction fields: %s", str(e))
        return False


def create_search_index():
    """Create search index for content text (PostgreSQL specific)"""
    try:
        logger.info("Creating search index for content text...")

        with db.engine.connect() as conn:
            # Create GIN index for full-text search (PostgreSQL)
            conn.execute(
                db.text(
                    """
                CREATE INDEX IF NOT EXISTS idx_filesystem_content_search 
                ON filesystem_items 
                USING GIN(to_tsvector('english', COALESCE(content_text, '')))
            """
                )
            )

            # Create regular index for name search
            conn.execute(
                db.text(
                    """
                CREATE INDEX IF NOT EXISTS idx_filesystem_name_search 
                ON filesystem_items 
                USING GIN(to_tsvector('english', name))
            """
                )
            )

            conn.commit()

        logger.info("Successfully created search indexes")
        return True

    except Exception as e:
        logger.error("Failed to create search indexes: %s", str(e))
        return False


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    # Import Flask app to get database context
    from app_factory import create_app

    app = create_app("operations")

    with app.app_context():
        logger.info("Starting database migration for content extraction...")

        success = True

        # Add new fields
        if not upgrade_database():
            success = False

        # Create search indexes
        if not create_search_index():
            success = False

        if success:
            logger.info("Database migration completed successfully!")
            sys.exit(0)
        else:
            logger.error("Database migration failed!")
            sys.exit(1)
