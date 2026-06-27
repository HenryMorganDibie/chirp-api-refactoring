"""Tests for comments_handler — gRPC CommentsService handler.

Uses mocked service functions and a mock gRPC context.
"""

from unittest.mock import MagicMock, patch

import pytest

from chirp_api.generated import comments_pb2
from chirp_api.handlers.comments_handler import CommentsServiceServicer


@pytest.fixture
def servicer():
    return CommentsServiceServicer()


@pytest.fixture
def context():
    return MagicMock()


@pytest.fixture
def valid_auth():
    return {"user_id": "user-123", "username": "testuser", "role": "user"}


class TestCreateComment:
    @patch("chirp_api.handlers.comments_handler.create_comment")
    @patch("chirp_api.handlers.comments_handler.validate_session_token")
    @patch("chirp_api.handlers.comments_handler.SessionLocal")
    def test_create_comment_success(
        self, mock_session_cls, mock_validate, mock_create, servicer, context, valid_auth
    ):
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_validate.return_value = valid_auth
        mock_create.return_value = {"comment_id": "comment-123"}

        request = comments_pb2.CreateCommentRequest(
            post_id="post-123",
            content="Nice post!",
            session_token="valid-token",
        )

        response = servicer.CreateComment(request, context)

        assert response.success is True
        assert response.comment_id == "comment-123"


class TestGetPostComments:
    @patch("chirp_api.handlers.comments_handler.get_post_comments")
    @patch("chirp_api.handlers.comments_handler.SessionLocal")
    def test_get_post_comments(self, mock_session_cls, mock_get_comments, servicer, context):
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_get_comments.return_value = [
            {
                "id": "comment-1",
                "content": "Comment 1",
                "created_at": 1700000000,
                "parent_id": None,
                "author": {
                    "id": "user-1",
                    "username": "user1",
                    "display_name": "User 1",
                    "avatar_url": None,
                },
                "like_count": 0,
                "is_liked": False,
                "replies": [],
            },
        ]

        request = comments_pb2.GetPostCommentsRequest(post_id="post-123")
        response = servicer.GetPostComments(request, context)

        assert len(response.comments) == 1
        assert response.comments[0].id == "comment-1"


class TestDeleteComment:
    @patch("chirp_api.handlers.comments_handler.delete_comment")
    @patch("chirp_api.handlers.comments_handler.validate_session_token")
    @patch("chirp_api.handlers.comments_handler.SessionLocal")
    def test_delete_comment_success(
        self, mock_session_cls, mock_validate, mock_delete, servicer, context, valid_auth
    ):
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_validate.return_value = valid_auth
        mock_delete.return_value = {"success": True}

        request = comments_pb2.DeleteCommentRequest(
            comment_id="comment-123",
            session_token="valid-token",
        )

        response = servicer.DeleteComment(request, context)

        assert response.success is True
