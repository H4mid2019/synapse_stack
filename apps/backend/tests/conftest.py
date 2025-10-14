import pytest

from app_factory import create_app
from database import db
from models import FileSystemItem, User


@pytest.fixture
def app():
    # Create a combined app with all blueprints for testing
    app = create_app("operations")  # Operations has all endpoints including health
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    # Register other blueprints for complete test coverage
    from routes_read import read_bp
    from routes_write import write_bp

    app.register_blueprint(read_bp, url_prefix="/api")
    app.register_blueprint(write_bp, url_prefix="/api")

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def sample_user(app):
    with app.app_context():
        user = User(
            auth0_id="test|123456",
            email="test@example.com",
            name="Test User"
        )
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def sample_item(app, sample_user):
    with app.app_context():
        item = FileSystemItem(
            name="Test Folder",
            type="folder",
            owner_id=sample_user.id,
            parent_id=None
        )
        db.session.add(item)
        db.session.commit()
        return item
