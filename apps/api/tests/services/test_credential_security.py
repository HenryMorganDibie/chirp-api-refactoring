import hashlib
import os

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
        old_hash = hashlib.sha256(("password" + "salt").encode()).hexdigest()
        assert _is_legacy_hash(old_hash) is True

    def test_bcrypt_hash_not_detected_as_legacy(self):
        new_hash = hash_password("password")
        assert _is_legacy_hash(new_hash) is False


class TestBcryptHashing:
    def test_new_hashes_use_bcrypt(self):
        hashed = hash_password("mysecretpassword")
        assert hashed.startswith("$2b$"), "Hash must be bcrypt format"
        assert len(hashed) == 60, "bcrypt hash is always 60 chars"

    def test_bcrypt_includes_random_salt(self):
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
        h1 = hash_password("password123")
        h2 = hash_password("password123")
        assert h1 != h2


class TestLegacyPasswordVerification:
    def test_legacy_sha256_password_still_verifies(self):
        old_hash = _legacy_hash("password123")
        assert verify_password("password123", old_hash) is True

    def test_legacy_sha256_wrong_password_rejected(self):
        old_hash = _legacy_hash("password123")
        assert verify_password("wrongpassword", old_hash) is False


class TestLegacyMigrationOnLogin:
    def test_login_migrates_legacy_hash_to_bcrypt(self, session):
        old_hash = _legacy_hash("password123")
        user = create_test_user(
            session,
            {"email": "legacy@example.com", "password_hash": old_hash},
        )
        assert _is_legacy_hash(user.password_hash)
        login_user(session, email="legacy@example.com", password="password123")
        session.refresh(user)
        assert not _is_legacy_hash(user.password_hash)
        assert user.password_hash.startswith("$2b$")

    def test_login_still_works_after_migration(self, session):
        old_hash = _legacy_hash("password123")
        create_test_user(
            session,
            {"email": "migrate2@example.com", "password_hash": old_hash},
        )
        login_user(session, email="migrate2@example.com", password="password123")
        result = login_user(session, email="migrate2@example.com", password="password123")
        assert result["session_token"] is not None


class TestNewRegistrationsUseBcrypt:
    def test_register_stores_bcrypt_hash(self, session):
        from chirp_api.db.models import User
        from sqlalchemy import select

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
        assert user.password_hash.startswith("$2b$")
        assert not _is_legacy_hash(user.password_hash)


class TestJWTSecretRequirement:
    def test_jwt_secret_is_set_in_test_environment(self):
        secret = os.environ.get("GRPC_JWT_SECRET", "")
        assert len(secret) > 0

    def test_jwt_tokens_are_signed_with_env_secret(self):
        import jwt as pyjwt

        from chirp_api.middleware.auth import JWT_SECRET, create_session_token

        token = create_session_token("user-1", "alice", "user")
        decoded = pyjwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        assert decoded["userId"] == "user-1"
        assert decoded["username"] == "alice"

    def test_token_signed_with_wrong_secret_is_rejected(self):
        import jwt as pyjwt

        from chirp_api.middleware.auth import validate_session_token

        fake_token = pyjwt.encode(
            {"userId": "u1", "username": "hacker", "role": "admin", "exp": 9999999999},
            "wrong-secret",
            algorithm="HS256",
        )
        with pytest.raises(Exception, match="Invalid or expired session token"):
            validate_session_token(fake_token)
