"""Tests for likes_handler — gRPC LikesService handler.

Uses mocked service functions and a mock gRPC context.
"""

from unittest.mock import MagicMock, patch

import pytest

from chirp_api.generated import likes_pb2
from chirp_api.handlers.likes_handler import LikesServiceServicer


@pytest.fixture
def servicer():
    return LikesServiceServicer()


@pytest.fixture
def context():
    return MagicMock()


@pytest.fixture
def valid_auth():
    return {"user_id": "user-123", "username": "testuser", "role": "user"}


class TestTogglePostLike:
    @patch("chirp_api.handlers.likes_handler.toggle_post_like")
    @patch("chirp_api.handlers.likes_handler.validate_session_token")
    @patch("chirp_api.handlers.likes_handler.SessionLocal")
    def test_toggle_post_like(
        self, mock_session_cls, mock_validate, mock_toggle, servicer, context, valid_auth
    ):
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_validate.return_value = valid_auth
        mock_toggle.return_value = {"liked": True}

        request = likes_pb2.TogglePostLikeRequest(
            post_id="post-123",
            session_token="valid-token",
        )

        response = servicer.TogglePostLike(request, context)

        assert response.success is True
        assert response.liked is True


class TestToggleCommentLike:
    @patch("chirp_api.handlers.likes_handler.toggle_comment_like")
    @patch("chirp_api.handlers.likes_handler.validate_session_token")
    @patch("chirp_api.handlers.likes_handler.SessionLocal")
    def test_toggle_comment_like(
        self, mock_session_cls, mock_validate, mock_toggle, servicer, context, valid_auth
    ):
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_validate.return_value = valid_auth
        mock_toggle.return_value = {"liked": True}

        request = likes_pb2.ToggleCommentLikeRequest(
            comment_id="comment-123",
            session_token="valid-token",
        )

        response = servicer.ToggleCommentLike(request, context)

        assert response.success is True
        assert response.liked is True


class TestGetPostLikeStatus:
    @patch("chirp_api.handlers.likes_handler.get_post_like_status")
    @patch("chirp_api.handlers.likes_handler.validate_session_token")
    @patch("chirp_api.handlers.likes_handler.SessionLocal")
    def test_get_post_like_status(
        self, mock_session_cls, mock_validate, mock_status, servicer, context, valid_auth
    ):
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_validate.return_value = valid_auth
        mock_status.return_value = {"liked": True}

        request = likes_pb2.GetLikeStatusRequest(
            post_id="post-123",
            session_token="valid-token",
        )

        response = servicer.GetPostLikeStatus(request, context)

        assert response.liked is True


class TestGetCommentLikeStatus:
    @patch("chirp_api.handlers.likes_handler.get_comment_like_status")
    @patch("chirp_api.handlers.likes_handler.validate_session_token")
    @patch("chirp_api.handlers.likes_handler.SessionLocal")
    def test_get_comment_like_status(
        self, mock_session_cls, mock_validate, mock_status, servicer, context, valid_auth
    ):
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_validate.return_value = valid_auth
        mock_status.return_value = {"liked": False}

        request = likes_pb2.GetCommentLikeStatusRequest(
            comment_id="comment-123",
            session_token="valid-token",
        )

        response = servicer.GetCommentLikeStatus(request, context)

        assert response.liked is False
