#!/usr/bin/env python3
"""
CockroachDB Connection Test Script

This script helps you test your CockroachDB connection before deploying.
"""

import os
import sys

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_connection():
    """Test database connection and print diagnostics."""

    database_uri = os.getenv("DATABASE_URL")

    if not database_uri:
        print("ERROR: DATABASE_URL not set in environment")
        print("\nSet it with:")
        print(
            "  export DATABASE_URL='cockroachdb://user:pass@host:26257/db?sslmode=verify-full'"
        )
        sys.exit(1)

    print("CockroachDB Connection Test")
    print("-" * 40)

    print(f"\nOriginal URI: {database_uri[:30]}...")

    # Apply conversion logic (same as app.py)
    converted_uri = database_uri

    if database_uri.startswith("cockroachdb://"):
        converted_uri = database_uri.replace(
            "cockroachdb://", "cockroachdb+psycopg2://"
        )
        print("Detected cockroachdb:// prefix")
    elif (
        "cockroachlabs.cloud" in database_uri
        or os.getenv("USE_COCKROACHDB", "").lower() == "true"
    ):
        if database_uri.startswith("postgresql://"):
            converted_uri = database_uri.replace(
                "postgresql://", "cockroachdb+psycopg2://"
            )
            print("Detected CockroachDB Cloud URI")

    print(f"Converted URI: {converted_uri[:40]}...")

    if "@" in database_uri:
        host_part = database_uri.split("@")[1].split("/")[0]
        print(f"Host: {host_part}")

    print("\nTesting connection...")

    try:
        from sqlalchemy import create_engine, text

        engine = create_engine(
            converted_uri,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=300,
        )

        with engine.connect() as connection:
            result = connection.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print("Connection successful")
            print(f"\nDatabase version: {version[:80]}...")

            result = connection.execute(text("SELECT 1 as test"))
            test_value = result.fetchone()[0]
            print(f"Test query successful (result: {test_value})")

            print("\nTesting table creation...")
            connection.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS _connection_test (id INT PRIMARY KEY, data TEXT)"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO _connection_test (id, data) VALUES (1, 'test') ON CONFLICT (id) DO NOTHING"
                )
            )
            connection.execute(text("DROP TABLE _connection_test"))
            connection.commit()
            print("Table operations successful")

        print("\nAll tests passed. CockroachDB is ready.")

    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("\nInstall required packages:")
        print("  pip install sqlalchemy-cockroachdb psycopg2-binary")
        sys.exit(1)

    except Exception as e:
        print("\nConnection failed")
        print(f"Error: {str(e)}")
        print("\nTroubleshooting:")
        print("  1. Check your DATABASE_URL is correct")
        print("  2. Verify sslmode=verify-full is in the URI")
        print("  3. Check your IP is whitelisted in CockroachDB Cloud")
        print("  4. Verify username and password are correct")
        print("  5. See COCKROACHDB_SETUP.md for more help")
        sys.exit(1)


if __name__ == "__main__":
    test_connection()
