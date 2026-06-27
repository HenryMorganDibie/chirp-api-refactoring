"""Tests for admin_handler — gRPC AdminService handler.

Uses mocked service functions and a mock gRPC context.
All admin methods require admin authentication.
"""

from unittest.mock import MagicMock, patch

import pytest

from chirp_api.generated import admin_pb2, common_pb2
from chirp_api.handlers.admin_handler import AdminServiceServicer


@pytest.fixture
def servicer():
    return AdminServiceServicer()


@pytest.fixture
def context():
    return MagicMock()


@pytest.fixture
def admin_auth():
    return {"user_id": "admin-123", "username": "admin", "role": "admin"}


class TestListUsers:
    @patch("chirp_api.handlers.admin_handler.list_users")
    @patch("chirp_api.handlers.admin_handler.require_admin")
    @patch("chirp_api.handlers.admin_handler.validate_session_token")
    @patch("chirp_api.handlers.admin_handler.SessionLocal")
    def test_list_users(
        self,
        mock_session_cls,
        mock_validate,
        mock_require,
        mock_list,
        servicer,
        context,
        admin_auth,
    ):
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_validate.return_value = admin_auth
        mock_list.return_value = {
            "users": [
                {
                    "id": "user-1",
                    "email": "user1@example.com",
                    "username": "user1",
                    "display_name": "User 1",
                    "avatar_url": None,
                    "bio": None,
                    "role": "user",
                    "created_at": 1700000000,
                    "updated_at": 1700000000,
                    "banned_at": None,
                    "banned_reason": None,
                    "post_count": 5,
                    "comment_count": 3,
                },
            ],
            "total": 1,
        }

        request = admin_pb2.ListUsersRequest(
            session_token="admin-token",
            pagination=common_pb2.PaginationRequest(limit=20, offset=0),
        )

        response = servicer.ListUsers(request, context)

        assert response.total == 1
        assert len(response.users) == 1
        assert response.users[0].username == "user1"


class TestBanUser:
    @patch("chirp_api.handlers.admin_handler.ban_user")
    @patch("chirp_api.handlers.admin_handler.require_admin")
    @patch("chirp_api.handlers.admin_handler.validate_session_token")
    @patch("chirp_api.handlers.admin_handler.SessionLocal")
    def test_ban_user(
        self, mock_session_cls, mock_validate, mock_require, mock_ban, servicer, context, admin_auth
    ):
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_validate.return_value = admin_auth
        mock_ban.return_value = {"success": True}

        request = admin_pb2.BanUserRequest(
            session_token="admin-token",
            user_id="user-1",
            reason="Spamming",
        )

        response = servicer.BanUser(request, context)

        assert response.success is True


class TestUnbanUser:
    @patch("chirp_api.handlers.admin_handler.unban_user")
    @patch("chirp_api.handlers.admin_handler.require_admin")
    @patch("chirp_api.handlers.admin_handler.validate_session_token")
    @patch("chirp_api.handlers.admin_handler.SessionLocal")
    def test_unban_user(
        self,
        mock_session_cls,
        mock_validate,
        mock_require,
        mock_unban,
        servicer,
        context,
        admin_auth,
    ):
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_validate.return_value = admin_auth
        mock_unban.return_value = {"success": True}

        request = admin_pb2.UnbanUserRequest(
            session_token="admin-token",
            user_id="user-1",
        )

        response = servicer.UnbanUser(request, context)

        assert response.success is True


class TestUpdateUserRole:
    @patch("chirp_api.handlers.admin_handler.update_user_role")
    @patch("chirp_api.handlers.admin_handler.require_admin")
    @patch("chirp_api.handlers.admin_handler.validate_session_token")
    @patch("chirp_api.handlers.admin_handler.SessionLocal")
    def test_update_user_role(
        self,
        mock_session_cls,
        mock_validate,
        mock_require,
        mock_update,
        servicer,
        context,
        admin_auth,
    ):
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_validate.return_value = admin_auth
        mock_update.return_value = {"success": True}

        request = admin_pb2.UpdateUserRoleRequest(
            session_token="admin-token",
            user_id="user-1",
            role="moderator",
        )

        response = servicer.UpdateUserRole(request, context)

        assert response.success is True


class TestDeleteUser:
    @patch("chirp_api.handlers.admin_handler.delete_user")
    @patch("chirp_api.handlers.admin_handler.require_admin")
    @patch("chirp_api.handlers.admin_handler.validate_session_token")
    @patch("chirp_api.handlers.admin_handler.SessionLocal")
    def test_delete_user(
        self,
        mock_session_cls,
        mock_validate,
        mock_require,
        mock_delete,
        servicer,
        context,
        admin_auth,
    ):
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_validate.return_value = admin_auth
        mock_delete.return_value = {"success": True}

        request = admin_pb2.DeleteUserRequest(
            session_token="admin-token",
            user_id="user-1",
        )

        response = servicer.DeleteUser(request, context)

        assert response.success is True


class TestGetDashboardStats:
    @patch("chirp_api.handlers.admin_handler.get_dashboard_stats")
    @patch("chirp_api.handlers.admin_handler.require_admin")
    @patch("chirp_api.handlers.admin_handler.validate_session_token")
    @patch("chirp_api.handlers.admin_handler.SessionLocal")
    def test_get_dashboard_stats(
        self,
        mock_session_cls,
        mock_validate,
        mock_require,
        mock_stats,
        servicer,
        context,
        admin_auth,
    ):
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_validate.return_value = admin_auth
        mock_stats.return_value = {
            "total_users": 100,
            "total_posts": 500,
            "total_comments": 1200,
            "pending_reports": 5,
            "new_users_today": 10,
            "new_posts_today": 25,
            "banned_users": 3,
        }

        request = admin_pb2.GetDashboardStatsRequest(session_token="admin-token")
        response = servicer.GetDashboardStats(request, context)

        assert response.total_users == 100
        assert response.total_posts == 500
        assert response.total_comments == 1200
        assert response.pending_reports == 5
        assert response.banned_users == 3
