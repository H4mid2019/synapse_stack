"""Test fixtures.

Authentication runs through the real request path. The only thing stubbed is
verify_decode_jwt, the step that needs Auth0's signing keys. Header parsing,
error handling and the population of flask.g all behave as they do in
production.

The previous version set TEST_MODE=true, which made requires_auth skip
verification entirely. That put a bypass in shipped code, and its localhost
guard did not hold behind the nginx these processes run under.
"""

import pytest
from app_factory import create_app
from database import db
from flask.testing import FlaskClient
from models import FileSystemItem, User

OWNER = "auth0|owner"
OTHER = "auth0|other"
TOKEN_PREFIX = "token-for-"


def _payload_for(auth0_id):
    """What Auth0 would return for a valid token belonging to this subject."""
    handle = auth0_id.split("|")[-1]
    return {"sub": auth0_id, "email": f"{handle}@example.com", "name": handle}


class AuthedClient(FlaskClient):
    """Test client that presents a bearer token for a chosen subject."""

    auth0_id = OWNER

    def open(self, *args, **kwargs):
        headers = dict(kwargs.pop("headers", None) or {})
        headers.setdefault("Authorization", f"Bearer {TOKEN_PREFIX}{self.auth0_id}")
        kwargs["headers"] = headers
        return super().open(*args, **kwargs)


@pytest.fixture(autouse=True)
def stub_jwt_verification(monkeypatch):
    """Accept tokens shaped like "token-for-<auth0_id>", reject anything else.

    Rejecting unknown tokens keeps the tests honest about what a bad token does,
    rather than making every string valid.
    """
    import auth

    def fake_verify(token):
        if not token.startswith(TOKEN_PREFIX):
            raise auth.AuthError({"code": "invalid_token", "description": "bad token"}, 401)
        return _payload_for(token.removeprefix(TOKEN_PREFIX))

    monkeypatch.setattr(auth, "verify_decode_jwt", fake_verify)


@pytest.fixture(scope="function")
def app(tmp_path, monkeypatch):
    # A file, not sqlite:///:memory:. Each connection to an in-memory SQLite
    # gets its own empty database, so rows written by a fixture are invisible to
    # the request handler. Set before create_app, because that is where the
    # engine is bound.
    # as_posix, because a Windows path with backslashes does not survive being
    # pasted into a sqlite:/// URI.
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{(tmp_path / 'test.db').as_posix()}")

    app = create_app("operations")
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.test_client_class = AuthedClient

    from routes_read import read_bp
    from routes_write import write_bp

    app.register_blueprint(read_bp, url_prefix="/api")
    app.register_blueprint(write_bp, url_prefix="/api")

    with app.app_context():
        db.create_all()
        for auth0_id in (OWNER, OTHER):
            handle = auth0_id.split("|")[-1]
            db.session.add(User(auth0_id=auth0_id, email=f"{handle}@example.com", name=handle))
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Authenticated as OWNER."""
    return app.test_client()


@pytest.fixture
def other_client(app):
    """Authenticated as a different real user, for authorization tests."""
    app.test_client_class = type("OtherClient", (AuthedClient,), {"auth0_id": OTHER})
    try:
        yield app.test_client()
    finally:
        app.test_client_class = AuthedClient


@pytest.fixture
def anonymous_client(app):
    """No Authorization header at all."""
    app.test_client_class = FlaskClient
    try:
        yield app.test_client()
    finally:
        app.test_client_class = AuthedClient


@pytest.fixture
def sample_user(app):
    with app.app_context():
        return User.query.filter_by(auth0_id=OWNER).first()


@pytest.fixture
def sample_item(app):
    with app.app_context():
        user = User.query.filter_by(auth0_id=OWNER).first()
        item = FileSystemItem(name="Test Folder", type="folder", owner_id=user.id, parent_id=None)
        db.session.add(item)
        db.session.commit()
        db.session.refresh(item)
        return item


@pytest.fixture
def other_users_item(app):
    """A folder owned by OTHER, which OWNER must never be able to reach."""
    with app.app_context():
        owner = User.query.filter_by(auth0_id=OTHER).first()
        item = FileSystemItem(name="Private", type="folder", owner_id=owner.id, parent_id=None)
        db.session.add(item)
        db.session.commit()
        db.session.refresh(item)
        return item
