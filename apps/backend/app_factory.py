"""
Unified Flask app factory for all services
Creates read, write, or operations app based on config
"""

import logging
import os

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

from database import db, migrate

load_dotenv()


APP_CONFIGS = {
    "read": {
        "blueprint_module": "routes_read",
        "blueprint_name": "read_bp",
        "default_port": 6001,
        "name": "READ APP",
    },
    "write": {
        "blueprint_module": "routes_write",
        "blueprint_name": "write_bp",
        "default_port": 6002,
        "name": "WRITE APP",
    },
    "operations": {
        "blueprint_module": "routes_operations",
        "blueprint_name": "operations_bp",
        "default_port": 6003,
        "name": "OPERATIONS APP",
    },
}


def create_app(app_type="read"):
    """
    Create Flask app for specified type
    Args:
        app_type: 'read', 'write', or 'operations'
    """
    if app_type not in APP_CONFIGS:
        raise ValueError(
            f"Invalid app type: {app_type}. Choose from: {', '.join(APP_CONFIGS.keys())}"
        )

    config = APP_CONFIGS[app_type]

    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
    database_uri = os.getenv("DATABASE_URL", "sqlite:///app.db")

    # CockroachDB URI conversion
    if database_uri.startswith("cockroachdb://"):
        database_uri = database_uri.replace("cockroachdb://", "cockroachdb+psycopg2://")
    elif (
        "cockroachlabs.cloud" in database_uri
        or os.getenv("USE_COCKROACHDB", "").lower() == "true"
    ):
        if database_uri.startswith("postgresql://"):
            database_uri = database_uri.replace(
                "postgresql://", "cockroachdb+psycopg2://"
            )

    app.config["SQLALCHEMY_DATABASE_URI"] = database_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    if "cockroachdb" in database_uri:
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_size": 10,
            "max_overflow": 20,
            "pool_pre_ping": True,
            "pool_recycle": 300,
        }

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)
    logger.info(
        "[%s] Starting on port %s",
        config["name"],
        os.getenv("PORT", config["default_port"]),
    )

    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)

    with app.app_context():
        try:
            db.session.execute(db.text("SELECT 1"))
            logger.info("[OK] Database connection successful (%s)", config["name"])
        except Exception as e:
            logger.error("[ERROR] Database connection failed: %s", str(e))

    # Dynamic blueprint import
    blueprint_module = __import__(config["blueprint_module"])
    blueprint = getattr(blueprint_module, config["blueprint_name"])
    app.register_blueprint(blueprint, url_prefix="/api")

    return app


if __name__ == "__main__":
    import sys

    app_type = sys.argv[1] if len(sys.argv) > 1 else "read"
    app = create_app(app_type)
    port = int(os.getenv("PORT", APP_CONFIGS[app_type]["default_port"]))
    app.run(host="0.0.0.0", port=port, debug=True)
