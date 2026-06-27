"""Tests for auth_service — registration, login, and current user retrieval.

Uses real in-memory database via the session fixture. No mocking.
"""

import pytest

from chirp_api.services.auth_service import get_current_user, login_user, register_user
from chirp_api.services.utils import hash_password
from tests.helpers import create_test_user


class TestRegisterUser:
    def test_register_user_success(self, session):
        result = register_user(
            session,
            email="alice@example.com",
            username="alice",
            display_name="Alice",
            password="password123",
        )

        assert result["user_id"] is not None
        assert len(result["user_id"]) > 0
        assert result["session_token"] is not None
        assert len(result["session_token"]) > 0

    def test_register_duplicate_email(self, session):
        create_test_user(session, {"email": "dupe@example.com"})

        with pytest.raises(Exception, match="email already exists"):
            register_user(
                session,
                email="dupe@example.com",
                username="different-user",
                display_name="Different",
                password="password123",
            )

    def test_register_duplicate_username(self, session):
        create_test_user(session, {"username": "taken"})

        with pytest.raises(Exception, match="Username already taken"):
            register_user(
                session,
                email="new@example.com",
                username="taken",
                display_name="New User",
                password="password123",
            )


class TestLoginUser:
    def test_login_success(self, session):
        create_test_user(
            session,
            {
                "email": "login@example.com",
                "password_hash": hash_password("mypassword"),
            },
        )

        result = login_user(session, email="login@example.com", password="mypassword")

        assert result["user_id"] is not None
        assert result["session_token"] is not None

    def test_login_wrong_password(self, session):
        create_test_user(
            session,
            {
                "email": "login2@example.com",
                "password_hash": hash_password("correctpassword"),
            },
        )

        with pytest.raises(Exception, match="Invalid email or password"):
            login_user(session, email="login2@example.com", password="wrongpassword")

    def test_login_banned_user(self, session):
        import time

        create_test_user(
            session,
            {
                "email": "banned@example.com",
                "password_hash": hash_password("password123"),
                "banned_at": int(time.time()),
                "banned_reason": "Spamming",
            },
        )

        with pytest.raises(Exception, match="Account banned"):
            login_user(session, email="banned@example.com", password="password123")


class TestGetCurrentUser:
    def test_get_current_user(self, session):
        user = create_test_user(
            session,
            {
                "email": "current@example.com",
                "username": "currentuser",
                "display_name": "Current User",
            },
        )

        result = get_current_user(session, user.id)

        assert result["id"] == user.id
        assert result["email"] == "current@example.com"
        assert result["username"] == "currentuser"
        assert result["display_name"] == "Current User"
        assert result["role"] == "user"
