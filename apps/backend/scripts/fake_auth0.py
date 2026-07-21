"""A local stand-in for Auth0, for the end to end suite.

This exists so the backend never needs a mode that skips authentication. It
generates an RSA key at startup, serves a real JWKS document, and mints real
RS256 tokens. The backend verifies those tokens with the same code path it uses
against Auth0 in production, so the end to end run exercises signature checking,
audience and issuer validation, and expiry, rather than stepping over them.

    python scripts/fake_auth0.py --port 9999 --audience synapse-api

Then point the backend at it:

    AUTH0_JWKS_URL=http://localhost:9999/.well-known/jwks.json
    AUTH0_USERINFO_URL=http://localhost:9999/userinfo
    AUTH0_AUDIENCE=synapse-api
    AUTH0_DOMAIN=localhost:9999

GET /token?sub=auth0|someone returns a signed token for that subject, which is
how the browser tests obtain a credential.
"""

import argparse
import json
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import jwt
from jose.utils import base64url_encode

KEY_ID = "local-test-key"


def _int_to_b64(value: int) -> str:
    length = (value.bit_length() + 7) // 8
    return base64url_encode(value.to_bytes(length, "big")).decode()


class FakeAuth0:
    def __init__(self, issuer: str, audience: str):
        self.issuer = issuer
        self.audience = audience
        self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        numbers = self.private_key.public_key().public_numbers()
        self.jwks = {
            "keys": [
                {
                    "kty": "RSA",
                    "use": "sig",
                    "alg": "RS256",
                    "kid": KEY_ID,
                    "n": _int_to_b64(numbers.n),
                    "e": _int_to_b64(numbers.e),
                }
            ]
        }
        self._pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

    def mint(self, sub: str, ttl: int = 3600) -> str:
        handle = sub.split("|")[-1]
        now = int(time.time())
        claims = {
            "sub": sub,
            "email": f"{handle}@example.com",
            "name": handle,
            "aud": self.audience,
            "iss": self.issuer,
            "iat": now,
            "exp": now + ttl,
        }
        return jwt.encode(claims, self._pem, algorithm="RS256", headers={"kid": KEY_ID})


def make_handler(issuer: FakeAuth0):
    class Handler(BaseHTTPRequestHandler):
        def _send(self, payload, status=200):
            body = json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):  # noqa: N802  (BaseHTTPRequestHandler's naming)
            parsed = urlparse(self.path)

            if parsed.path == "/.well-known/jwks.json":
                self._send(issuer.jwks)
            elif parsed.path == "/token":
                params = parse_qs(parsed.query)
                sub = params.get("sub", ["auth0|e2e"])[0]
                self._send({"access_token": issuer.mint(sub), "token_type": "Bearer"})
            elif parsed.path == "/userinfo":
                auth = self.headers.get("Authorization", "")
                token = auth[7:] if auth.lower().startswith("bearer ") else ""
                try:
                    claims = jwt.get_unverified_claims(token)
                except Exception:  # noqa: BLE001  (any bad token is just a 401 here)
                    self._send({"error": "invalid token"}, status=401)
                    return
                self._send(
                    {
                        "sub": claims.get("sub"),
                        "email": claims.get("email"),
                        "name": claims.get("name"),
                    }
                )
            else:
                self._send({"error": "not found"}, status=404)

        def log_message(self, *args):
            """Quiet. The CI log is noisy enough."""

    return Handler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=9999)
    parser.add_argument("--audience", default="synapse-api")
    args = parser.parse_args()

    issuer = FakeAuth0(issuer=f"http://localhost:{args.port}/", audience=args.audience)
    server = HTTPServer(("127.0.0.1", args.port), make_handler(issuer))
    print(f"fake auth0 listening on http://127.0.0.1:{args.port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
