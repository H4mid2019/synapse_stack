"""
Unified bjoern runner for all Flask apps
Usage:
  python run_bjoern.py read
  python run_bjoern.py write
  python run_bjoern.py operations
"""

import sys
from os import getenv

import bjoern
from app_factory import APP_CONFIGS, create_app


def run_app(app_type):
    if app_type not in APP_CONFIGS:
        print(f"Invalid app type: {app_type}")
        print(f"Available: {', '.join(APP_CONFIGS.keys())}")
        sys.exit(1)

    config = APP_CONFIGS[app_type]
    app = create_app(app_type)

    SOCKET = getenv("SOCKET")
    PORT = int(getenv("PORT", config["default_port"]))

    if SOCKET:
        print(f"[{config['name']}] Serving from socket {SOCKET}")
        bjoern.run(app, f"unix:{SOCKET}")
    else:
        print(f"[{config['name']}] Serving from TCP port {PORT}")
        bjoern.run(app, "0.0.0.0", PORT)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_bjoern.py [read|write|operations]")
        sys.exit(1)

    app_type = sys.argv[1].lower()
    run_app(app_type)
