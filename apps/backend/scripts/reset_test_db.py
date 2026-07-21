"""Reset the database for an end to end run.

This exists so the application does not have to. The browser suite used to reset
state by POSTing to /api/test/reset-database, an unauthenticated endpoint that
called drop_all, which meant shipping a remote "destroy everything" button to
have a repeatable test run. A harness should set up its own fixtures out of
band, against the database, not through the app.

    DATABASE_URL=postgresql://... python scripts/reset_test_db.py
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app_factory import create_app  # noqa: E402
from database import db  # noqa: E402


def main():
    if not os.getenv("DATABASE_URL"):
        print("DATABASE_URL is not set", file=sys.stderr)
        return 1

    app = create_app("operations")
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("test database reset")
    return 0


if __name__ == "__main__":
    sys.exit(main())
