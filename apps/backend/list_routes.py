"""List all routes across the multi-app architecture"""
import sys

sys.path.insert(0, "apps/backend")

from app_factory import create_app  # noqa: E402
from routes_read import read_bp  # noqa: E402
from routes_write import write_bp  # noqa: E402

# Create operations app which has all blueprints registered
app = create_app("operations")

# Register other blueprints to show all routes
app.register_blueprint(read_bp, url_prefix="/api")
app.register_blueprint(write_bp, url_prefix="/api")

app.register_blueprint(read_bp, url_prefix="/api")
app.register_blueprint(write_bp, url_prefix="/api")

print("\nRegistered Routes Across All Apps:")
print("-" * 80)
for rule in app.url_map.iter_rules():
    if rule.endpoint != "static":
        methods = list(rule.methods - {"OPTIONS", "HEAD"})
        print(f"{rule.endpoint:40} {str(methods):20} {rule.rule}")
