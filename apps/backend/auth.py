"""Auth0 authentication utilities for Flask API"""

import json
import os
from functools import wraps
from urllib.request import Request, urlopen

from flask import g, jsonify, request
from jose import jwt

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
API_AUDIENCE = os.getenv("AUTH0_AUDIENCE")
ALGORITHMS = ["RS256"]
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"
FLASK_ENV = os.getenv("FLASK_ENV", "development")
TEST_ALLOWED_IPS = ["127.0.0.1", "localhost", "::1"]

if TEST_MODE and FLASK_ENV == "production":
    raise RuntimeError(
        "TEST_MODE cannot be enabled in production environment. " "Set FLASK_ENV=development or disable TEST_MODE."
    )


class AuthError(Exception):
    """Custom Auth Error"""

    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


def get_token_auth_header():
    """Obtains the Access Token from the Authorization Header"""
    auth = request.headers.get("Authorization", None)
    if not auth:
        raise AuthError(
            {
                "code": "authorization_header_missing",
                "description": "Authorization header is expected",
            },
            401,
        )

    parts = auth.split()

    if parts[0].lower() != "bearer":
        raise AuthError(
            {
                "code": "invalid_header",
                "description": "Authorization header must start with Bearer",
            },
            401,
        )
    elif len(parts) == 1:
        raise AuthError({"code": "invalid_header", "description": "Token not found"}, 401)
    elif len(parts) > 2:
        raise AuthError(
            {
                "code": "invalid_header",
                "description": "Authorization header must be Bearer token",
            },
            401,
        )

    token = parts[1]
    return token


def verify_decode_jwt(token):
    """Verifies and decodes JWT token from Auth0"""
    jsonurl = urlopen(f"https://{AUTH0_DOMAIN}/.well-known/jwks.json")
    jwks = json.loads(jsonurl.read())

    try:
        unverified_header = jwt.get_unverified_header(token)
    except jwt.JWTError as e:
        raise AuthError({"code": "invalid_header", "description": f"Invalid header: {str(e)}"}, 401)

    if unverified_header.get("alg") == "HS256":
        raise AuthError(
            {
                "code": "invalid_header",
                "description": "Invalid header. Use an RS256 signed JWT Access Token",
            },
            401,
        )

    rsa_key = {}
    for key in jwks["keys"]:
        if key["kid"] == unverified_header["kid"]:
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"],
            }
            break

    if rsa_key:
        try:
            # Decode with or without audience based on whether API_AUDIENCE is set
            decode_options = {
                "algorithms": ALGORITHMS,
                "issuer": f"https://{AUTH0_DOMAIN}/",
            }
            if API_AUDIENCE:
                decode_options["audience"] = API_AUDIENCE

            payload = jwt.decode(token, rsa_key, **decode_options)
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthError({"code": "token_expired", "description": "Token is expired"}, 401)
        except jwt.JWTClaimsError as e:
            raise AuthError(
                {
                    "code": "invalid_claims",
                    "description": f"Incorrect claims: {str(e)}. Check audience and issuer",
                },
                401,
            )
        except Exception as e:
            raise AuthError(
                {
                    "code": "invalid_header",
                    "description": f"Unable to parse authentication token: {str(e)}",
                },
                401,
            )

    raise AuthError({"code": "invalid_header", "description": "Unable to find appropriate key"}, 401)


def requires_auth(f):
    """Decorator to require authentication for API endpoints"""

    @wraps(f)
    def decorated(*args, **kwargs):
        if TEST_MODE:
            client_ip = request.remote_addr
            if client_ip not in TEST_ALLOWED_IPS:
                return (
                    jsonify(
                        {
                            "code": "forbidden",
                            "description": f"Test mode only allowed from localhost. Your IP: {client_ip}",
                        }
                    ),
                    403,
                )

            g.current_user_auth0_id = "test|12345"
            g.current_user_email = "test@example.com"
            g.current_user_name = "Test User"
            return f(*args, **kwargs)

        try:
            token = get_token_auth_header()
            payload = verify_decode_jwt(token)
            g.current_user_auth0_id = payload.get("sub")
            g.current_user_email = payload.get("email")
            g.current_user_name = payload.get("name")
        except AuthError as e:
            return jsonify(e.error), e.status_code
        except Exception as e:
            return jsonify({"code": "invalid_token", "description": str(e)}), 401

        return f(*args, **kwargs)

    return decorated


def get_or_create_user(db, User):
    """Get or create user from Auth0 token payload"""
    auth0_id = g.current_user_auth0_id

    user = User.query.filter_by(auth0_id=auth0_id).first()

    if not user:
        # Get user info from Auth0 userinfo endpoint
        try:
            token = get_token_auth_header()
            userinfo_url = f"https://{AUTH0_DOMAIN}/userinfo"
            req = Request(userinfo_url)
            req.add_header("Authorization", f"Bearer {token}")

            userinfo_response = urlopen(req)
            userinfo = json.loads(userinfo_response.read())

            email = userinfo.get("email")
            name = userinfo.get("name") or userinfo.get("nickname") or email
            picture = userinfo.get("picture")
        except Exception:
            # Fallback if userinfo fails
            email = g.current_user_email or f"{auth0_id.split('|')[1]}@auth0.user"
            name = g.current_user_name or auth0_id.split("|")[1]
            picture = None

        # Create new user
        user = User(auth0_id=auth0_id, email=email, name=name, picture=picture)
        db.session.add(user)
        db.session.commit()
    else:
        # Update last login
        user.last_login = db.func.current_timestamp()
        db.session.commit()

    return user


def requires_permission(permission):
    """Decorator to check if user has permission for a file/folder"""

    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # This will be implemented based on your business logic
            # Check if user owns the file or has been granted permission
            return f(*args, **kwargs)

        return decorated

    return decorator
