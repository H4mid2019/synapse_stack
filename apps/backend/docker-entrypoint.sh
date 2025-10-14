#!/bin/bash
set -e

echo "Initializing database tables..."
python init_db.py

echo "Starting supervisor..."
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
