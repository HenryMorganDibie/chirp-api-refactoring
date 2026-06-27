"""JWT authentication middleware for Chirp API.

Uses PyJWT with HS256 signing.

SECURITY NOTE (Issue 1 — Trust Establishment):
  Previously, GRPC_JWT_SECRET fell back to a hardcoded string
  "chirp-grpc-jwt-secret-key-at-least-32-chars" if the env var was unset.
  Any developer, contractor, or attacker with code access could forge
  valid JWTs for any user, including admins, by signing with the known
  fallback secret. This is a critical authentication bypass.

  Fix: if GRPC_JWT_SECRET is not set in the environment, the server
  raises a RuntimeError at startup instead of silently using a known
  insecure default. A secure secret must be explicitly provisioned.

  For local development and tests, set GRPC_JWT_SECRET in your .env or
  the test environment. The test suite sets a test-specific value.
"""

import os
import time

import jwt

_raw_secret = os.environ.get("GRPC_JWT_SECRET", "")

# In test environments a placeholder is acceptable; in production the env var
# must be set to a strong random value. We detect the test sentinel below.
_TEST_SENTINEL = "test-jwt-secret-for-unit-tests"

if not _raw_secret:
    # Allow tests that explicitly patch this module to still work, but
    # fail fast in any real deployment where the secret was forgotten.
    # We raise at import time so the server never starts without a secret.
    raise RuntimeError(
        "GRPC_JWT_SECRET environment variable is not set. "
        "Generate a strong random secret and set it before starting the server. "
        "Example: export GRPC_JWT_SECRET=$(openssl rand -hex 32)"
    )

JWT_SECRET = _raw_secret

TOKEN_EXPIRY_SECONDS = 7 * 24 * 60 * 60  # 7 days


def validate_session_token(token: str) -> dict:
    """Validate a session token and return the auth context.

    Returns dict with userId, username, role.
    Raises Exception if token is invalid or expired.
    """
    assert isinstance(token, str), "Token must be a string"
    assert len(token) > 0, "Token must not be empty"

    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        result = {
            "user_id": decoded["userId"],
            "username": decoded["username"],
            "role": decoded["role"],
        }
        assert result["user_id"], "Token must contain userId"
        assert result["username"], "Token must contain username"
        assert result["role"], "Token must contain role"
        return result
    except jwt.ExpiredSignatureError:
        raise Exception("Invalid or expired session token")
    except jwt.InvalidTokenError:
        raise Exception("Invalid or expired session token")
    except KeyError:
        raise Exception("Invalid or expired session token")


def create_session_token(
    user_id: str, username: str, role: str, expires_in_seconds: int = TOKEN_EXPIRY_SECONDS
) -> str:
    """Create a session token from user info.

    Returns JWT string.
    """
    assert isinstance(user_id, str) and len(user_id) > 0, "user_id must be a non-empty string"
    assert isinstance(username, str) and len(username) > 0, "username must be a non-empty string"
    assert role in ("user", "admin", "moderator"), f"Invalid role: {role}"

    payload = {
        "userId": user_id,
        "username": username,
        "role": role,
        "exp": int(time.time()) + expires_in_seconds,
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    assert isinstance(token, str), "Encoded token must be a string"
    return token


def require_auth(token: str | None) -> dict:
    """Require authentication. Raises Exception if token is missing or invalid.

    Returns auth context dict with userId, username, role.
    """
    if not token:
        raise Exception("Authentication required")
    return validate_session_token(token)


def require_admin(context: dict) -> None:
    """Require admin or moderator role. Raises Exception if not authorized."""
    assert isinstance(context, dict), "Context must be a dict"
    if context.get("role") not in ("admin", "moderator"):
        raise Exception("Admin access required")


def require_super_admin(context: dict) -> None:
    """Require admin role specifically. Raises Exception if not authorized."""
    assert isinstance(context, dict), "Context must be a dict"
    if context.get("role") != "admin":
        raise Exception("Super admin access required")
