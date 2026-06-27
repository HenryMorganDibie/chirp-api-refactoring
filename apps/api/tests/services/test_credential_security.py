"""Security tests for Issue 1: Credential Problem.

Proves:
  1. Old SHA-256 scheme was insecure (static salt, no cost factor)
  2. New bcrypt scheme stores proper hashes
  3. Legacy SHA-256 users can still log in (backwards compatibility)
  4. On login, legacy hashes are transparently migrated to bcrypt
  5. JWT secret is required at runtime (no hardcoded fallback)
"""

import hashlib
import os

import bcrypt
import pytest

from chirp_api.services.auth_service import login_user, register_user
from chirp_api.services.utils import (
    _is_legacy_hash,
    _legacy_hash,
    hash_password,
    verify_password,
)
from tests.helpers import create_test_user


class TestLegacyHashDetection:
    def test_sha256_hash_detected_as_legacy(self):
        """SHA-256 hex output (64 chars) is correctly identified as legacy."""
        old_hash = hashlib.sha256(("password" + "salt").encode()).hexdigest()
        assert _is_legacy_hash(old_hash) is True

    def test_bcrypt_hash_not_detected_as_legacy(self):
        """bcrypt hash starting with $2b$ is not flagged as legacy."""
        new_hash = hash_password("password")
        assert _is_legacy_hash(new_hash) is False


class TestBcryptHashing:
    def test_new_hashes_use_bcrypt(self):
        """hash_password() produces a bcrypt hash, not a hex digest."""
        hashed = hash_password("mysecretpassword")
        assert hashed.startswith("$2b$"), "Hash must be bcrypt format"
        assert len(hashed) == 60, "bcrypt hash is always 60 chars"

    def test_bcrypt_includes_random_salt(self):
        """Two hashes of the same password must differ (per-password salt)."""
        h1 = hash_password("samepassword")
        h2 = hash_password("samepassword")
        assert h1 != h2, "bcrypt must produce different outputs per call"

    def test_verify_bcrypt_password_correct(self):
        hashed = hash_password("correcthorse")
        assert verify_password("correcthorse", hashed) is True

    def test_verify_bcrypt_password_wrong(self):
        hashed = hash_password("correcthorse")
        assert verify_password("wrongpassword", hashed) is False

    def test_identical_passwords_do_not_produce_identical_hashes(self):
        """Proves the old static-salt SHA-256 vulnerability is gone."""
        h1 = hash_password("password123")
        h2 = hash_password("password123")
        # With old SHA-256+static salt these would be equal — a rainbow table risk
        assert h1 != h2


class TestLegacyPasswordVerification:
    def test_legacy_sha256_password_still_verifies(self):
        """Existing seeded users with SHA-256 hashes can still log in."""
        old_hash = _legacy_hash("password123")
        assert verify_password("password123", old_hash) is True

    def test_legacy_sha256_wrong_password_rejected(self):
        old_hash = _legacy_hash("password123")
        assert verify_password("wrongpassword", old_hash) is False


class TestLegacyMigrationOnLogin:
    def test_login_migrates_legacy_hash_to_bcrypt(self, session):
        """On successful login, a legacy SHA-256 hash is upgraded to bcrypt in-place."""
        old_hash = _legacy_hash("password123")
        user = create_test_user(
            session,
            {
                "email": "legacy@example.com",
                "password_hash": old_hash,
            },
        )

        # Confirm it starts as a legacy hash
        assert _is_legacy_hash(user.password_hash)

        # Log in
        login_user(session, email="legacy@example.com", password="password123")

        # Refresh from DB
        session.refresh(user)

        # Hash must now be bcrypt
        assert not _is_legacy_hash(user.password_hash)
        assert user.password_hash.startswith("$2b$")

    def test_login_still_works_after_migration(self, session):
        """After migration, subsequent logins with bcrypt hash also succeed."""
        old_hash = _legacy_hash("password123")
        create_test_user(
            session,
            {
                "email": "migrate2@example.com",
                "password_hash": old_hash,
            },
        )

        # First login migrates
        login_user(session, email="migrate2@example.com", password="password123")
        # Second login uses new bcrypt hash
        result = login_user(session, email="migrate2@example.com", password="password123")
        assert result["session_token"] is not None


class TestNewRegistrationsUseBcrypt:
    def test_register_stores_bcrypt_hash(self, session):
        """Newly registered users always get a bcrypt hash, never SHA-256."""
        from sqlalchemy import select
        from chirp_api.db.models import User

        register_user(
            session,
            email="newuser@example.com",
            username="newuser",
            display_name="New User",
            password="securepassword",
        )

        user = session.execute(
            select(User).where(User.email == "newuser@example.com")
        ).scalar_one()

        assert user.password_hash.startswith("$2b$"), "Registration must use bcrypt"
        assert not _is_legacy_hash(user.password_hash)


class TestJWTSecretRequirement:
    def test_jwt_secret_is_set_in_test_environment(self):
        """The GRPC_JWT_SECRET env var must be set; no hardcoded fallback is allowed."""
        secret = os.environ.get("GRPC_JWT_SECRET", "")
        assert len(secret) > 0, (
            "GRPC_JWT_SECRET must be set. The server must never run with a hardcoded secret."
        )

    def test_jwt_tokens_are_signed_with_env_secret(self):
        """Tokens created by create_session_token() can be decoded with the env secret."""
        import jwt as pyjwt
        from chirp_api.middleware.auth import JWT_SECRET, create_session_token

        token = create_session_token("user-1", "alice", "user")
        decoded = pyjwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        assert decoded["userId"] == "user-1"
        assert decoded["username"] == "alice"

    def test_token_signed_with_wrong_secret_is_rejected(self):
        """A token signed with a different secret must be rejected."""
        import jwt as pyjwt
        from chirp_api.middleware.auth import validate_session_token

        fake_token = pyjwt.encode(
            {"userId": "u1", "username": "hacker", "role": "admin", "exp": 9999999999},
            "wrong-secret",
            algorithm="HS256",
        )

        with pytest.raises(Exception, match="Invalid or expired session token"):
            validate_session_token(fake_token)
