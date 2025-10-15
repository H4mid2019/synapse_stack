"""
Enhanced local development startup script
Starts all backend services including text extraction
"""

import logging
import os
import signal
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(message)s")
logger = logging.getLogger("LocalDev")

# Service configurations
SERVICES = {
    "proxy": {
        "cmd": ["python", "local_proxy.py"],
        "port": 5000,
        "description": "API Proxy & Load Balancer",
    },
    "read": {
        "cmd": [
            "python",
            "-c",
            "from app_factory import create_app; create_app('read').run(host='0.0.0.0', port=6001, debug=False)",
        ],
        "port": 6001,
        "description": "Read Service",
    },
    "write": {
        "cmd": [
            "python",
            "-c",
            "from app_factory import create_app; create_app('write').run(host='0.0.0.0', port=6002, debug=False)",
        ],
        "port": 6002,
        "description": "Write Service",
    },
    "operations": {
        "cmd": [
            "python",
            "-c",
            "from app_factory import create_app; create_app('operations').run(host='0.0.0.0', port=6003, debug=False)",
        ],
        "port": 6003,
        "description": "Operations Service",
    },
    "text_extractor": {
        "cmd": ["python", "text_extractor.py"],
        "port": 6004,
        "description": "Text Extraction Service",
    },
}

# Store process handles
processes = {}
should_exit = False


def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    global should_exit
    logger.info("Received interrupt signal, shutting down services...")
    should_exit = True


def start_service(name, config):
    """Start a single service"""
    try:
        logger.info(f"Starting {config['description']} on port {config['port']}")

        process = subprocess.Popen(
            config["cmd"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=1
        )

        processes[name] = process

        # Stream output
        for line in iter(process.stdout.readline, ""):
            if should_exit:
                break
            print(f"[{name.upper()}] {line.rstrip()}")

        process.wait()

    except Exception as e:
        logger.error(f"Error starting {name}: {e}")


def check_database():
    """Check if database is ready and has required tables"""
    try:
        # Use the same database config as the main app
        import os

        from dotenv import load_dotenv

        load_dotenv()
        database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:5432/flask_react_db")

        # Parse the database URL
        if database_url.startswith("postgresql://"):
            # Extract connection details from URL
            import re

            match = re.match(r"postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)", database_url)
            if not match:
                logger.error("Invalid DATABASE_URL format")
                return False

            user, password, host, port, dbname = match.groups()

            import psycopg2

            conn = psycopg2.connect(host=host, database=dbname, user=user, password=password, port=port)

            # Check if required tables exist
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'filesystem_items'
                );
            """
            )

            table_exists = cursor.fetchone()[0]
            cursor.close()
            conn.close()

            if not table_exists:
                logger.error("Database tables not found. Please run database setup first.")
                return False

            logger.info("Database connection and tables verified")
            return True
        else:
            logger.error("Unsupported database URL format")
            return False

    except Exception as e:
        logger.error(f"Database not ready: {e}")
        return False


def main():
    """Main function to start all services"""
    # Setup signal handling
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("Starting Flask React App Development Environment")
    logger.info("=" * 60)

    # Check database
    if not check_database():
        logger.error("Database is not available or missing tables.")
        logger.info("Attempting to run database setup...")

        try:
            # Run database setup
            setup_result = subprocess.run(["python", "setup_database.py"], capture_output=True, text=True, timeout=60)

            if setup_result.returncode == 0:
                logger.info("Database setup completed successfully")

                # Run content fields migration
                migration_result = subprocess.run(
                    ["python", "migrate_content_fields.py"], capture_output=True, text=True, timeout=30
                )

                if migration_result.returncode == 0:
                    logger.info("Content fields migration completed")
                else:
                    logger.warning(f"Migration warning: {migration_result.stderr}")
            else:
                logger.error(f"Database setup failed: {setup_result.stderr}")
                sys.exit(1)

        except Exception as e:
            logger.error(f"Error running database setup: {e}")
            sys.exit(1)

    # Start services
    try:
        with ThreadPoolExecutor(max_workers=len(SERVICES)) as executor:
            futures = {}

            for name, config in SERVICES.items():
                future = executor.submit(start_service, name, config)
                futures[name] = future
                time.sleep(1)  # Stagger startup

            logger.info("All services started! Available endpoints:")
            logger.info("- API Proxy: http://localhost:5000")
            logger.info("- Read Service: http://localhost:6001")
            logger.info("- Write Service: http://localhost:6002")
            logger.info("- Operations Service: http://localhost:6003")
            logger.info("- Text Extraction: http://localhost:6004")
            logger.info("Press Ctrl+C to stop all services")

            # Wait for completion or interruption
            for name, future in futures.items():
                if not should_exit:
                    try:
                        future.result()
                    except Exception as e:
                        logger.error(f"Service {name} failed: {e}")

    except KeyboardInterrupt:
        logger.info("Received KeyboardInterrupt")

    finally:
        # Cleanup
        logger.info("Stopping all services...")
        for name, process in processes.items():
            if process and process.poll() is None:
                logger.info(f"Terminating {name}")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning(f"Force killing {name}")
                    process.kill()

        logger.info("All services stopped")


if __name__ == "__main__":
    main()
