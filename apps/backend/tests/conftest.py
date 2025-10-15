import os

import pytest

os.environ["TEST_MODE"] = "true"

from app_factory import create_app  # noqa: E402
from database import db  # noqa: E402
from models import FileSystemItem, User  # noqa: E402


@pytest.fixture(scope="function")
def app():
    # Create a combined app with all blueprints for testing
    app = create_app("operations")  # Operations has all endpoints including health
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Register other blueprints for complete test coverage
    from routes_read import read_bp
    from routes_write import write_bp

    app.register_blueprint(read_bp, url_prefix="/api")
    app.register_blueprint(write_bp, url_prefix="/api")

    with app.app_context():
        db.create_all()

        # Create default test user
        user = User.query.filter_by(auth0_id="test|12345").first()
        if not user:
            user = User(auth0_id="test|12345", email="test@example.com", name="Test User")
            db.session.add(user)
            db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def sample_user(app):
    with app.app_context():
        user = User.query.filter_by(auth0_id="test|12345").first()
        return user


@pytest.fixture
def sample_item(app):
    with app.app_context():
        user = User.query.filter_by(auth0_id="test|12345").first()
        item = FileSystemItem(name="Test Folder", type="folder", owner_id=user.id, parent_id=None)
        db.session.add(item)
        db.session.commit()
        db.session.refresh(item)
        return item
