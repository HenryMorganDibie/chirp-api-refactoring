"""Tests for auth_handler — gRPC AuthService handler.

Uses mocked service functions and a mock gRPC context.
"""

from unittest.mock import MagicMock, patch

import pytest

from chirp_api.generated import auth_pb2
from chirp_api.handlers.auth_handler import AuthServiceServicer


@pytest.fixture
def servicer():
    return AuthServiceServicer()


@pytest.fixture
def context():
    ctx = MagicMock()
    ctx.abort = MagicMock(side_effect=Exception("aborted"))
    return ctx


class TestRegister:
    @patch("chirp_api.handlers.auth_handler.register_user")
    @patch("chirp_api.handlers.auth_handler.SessionLocal")
    def test_register_success(self, mock_session_cls, mock_register, servicer, context):
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_register.return_value = {
            "user_id": "user-123",
            "session_token": "token-abc",
        }

        request = auth_pb2.RegisterRequest(
            email="test@example.com",
            username="testuser",
            display_name="Test User",
            password="password123",
        )

        response = servicer.Register(request, context)

        assert response.success is True
        assert response.user_id == "user-123"
        assert response.session_token == "token-abc"

    @patch("chirp_api.handlers.auth_handler.register_user")
    @patch("chirp_api.handlers.auth_handler.SessionLocal")
    def test_register_duplicate_email(self, mock_session_cls, mock_register, servicer, context):
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_register.side_effect = Exception("User with this email already exists")

        request = auth_pb2.RegisterRequest(
            email="dupe@example.com",
            username="testuser",
            display_name="Test User",
            password="password123",
        )

        response = servicer.Register(request, context)

        assert response.success is False
        assert "email already exists" in response.error


class TestLogin:
    @patch("chirp_api.handlers.auth_handler.login_user")
    @patch("chirp_api.handlers.auth_handler.SessionLocal")
    def test_login_success(self, mock_session_cls, mock_login, servicer, context):
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_login.return_value = {
            "user_id": "user-123",
            "session_token": "token-abc",
        }

        request = auth_pb2.LoginRequest(
            email="test@example.com",
            password="password123",
        )

        response = servicer.Login(request, context)

        assert response.success is True
        assert response.user_id == "user-123"

    @patch("chirp_api.handlers.auth_handler.login_user")
    @patch("chirp_api.handlers.auth_handler.SessionLocal")
    def test_login_wrong_password(self, mock_session_cls, mock_login, servicer, context):
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_login.side_effect = Exception("Invalid email or password")

        request = auth_pb2.LoginRequest(
            email="test@example.com",
            password="wrong",
        )

        response = servicer.Login(request, context)

        assert response.success is False
        assert "Invalid email or password" in response.error


class TestLogout:
    def test_logout_returns_success(self, servicer, context):
        request = auth_pb2.LogoutRequest(session_token="any-token")
        response = servicer.Logout(request, context)

        assert response.success is True


class TestGetCurrentUser:
    @patch("chirp_api.handlers.auth_handler.get_current_user")
    @patch("chirp_api.handlers.auth_handler.validate_session_token")
    @patch("chirp_api.handlers.auth_handler.SessionLocal")
    def test_get_current_user_success(
        self, mock_session_cls, mock_validate, mock_get_user, servicer, context
    ):
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_validate.return_value = {
            "user_id": "user-123",
            "username": "testuser",
            "role": "user",
        }
        mock_get_user.return_value = {
            "id": "user-123",
            "email": "test@example.com",
            "username": "testuser",
            "display_name": "Test User",
            "avatar_url": None,
            "bio": None,
            "role": "user",
            "created_at": 1700000000,
        }

        request = auth_pb2.GetCurrentUserRequest(session_token="valid-token")
        response = servicer.GetCurrentUser(request, context)

        assert response.id == "user-123"
        assert response.username == "testuser"

    @patch("chirp_api.handlers.auth_handler.validate_session_token")
    def test_get_current_user_invalid_token(self, mock_validate, servicer, context):
        mock_validate.side_effect = Exception("Invalid or expired session token")

        request = auth_pb2.GetCurrentUserRequest(session_token="bad-token")

        with pytest.raises(Exception):
            servicer.GetCurrentUser(request, context)

        context.abort.assert_called_once()


class TestValidateSession:
    @patch("chirp_api.handlers.auth_handler.validate_session_token")
    def test_validate_session_valid(self, mock_validate, servicer, context):
        mock_validate.return_value = {
            "user_id": "user-123",
            "username": "testuser",
            "role": "user",
        }

        request = auth_pb2.ValidateSessionRequest(session_token="valid-token")
        response = servicer.ValidateSession(request, context)

        assert response.valid is True
        assert response.user_id == "user-123"
        assert response.username == "testuser"
        assert response.role == "user"

    @patch("chirp_api.handlers.auth_handler.validate_session_token")
    def test_validate_session_invalid(self, mock_validate, servicer, context):
        mock_validate.side_effect = Exception("Invalid token")

        request = auth_pb2.ValidateSessionRequest(session_token="bad-token")
        response = servicer.ValidateSession(request, context)

        assert response.valid is False
        assert response.user_id == ""
