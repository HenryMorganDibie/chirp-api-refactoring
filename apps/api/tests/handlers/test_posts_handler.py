"""Tests for posts_handler — gRPC PostsService handler.

Uses mocked service functions and a mock gRPC context.
"""

from unittest.mock import MagicMock, patch

import pytest

from chirp_api.generated import posts_pb2
from chirp_api.generated.common_pb2 import PaginationRequest
from chirp_api.handlers.posts_handler import PostsServiceServicer


@pytest.fixture
def servicer():
    return PostsServiceServicer()


@pytest.fixture
def context():
    return MagicMock()


@pytest.fixture
def valid_auth():
    return {"user_id": "user-123", "username": "testuser", "role": "user"}


class TestCreatePost:
    @patch("chirp_api.handlers.posts_handler.create_post")
    @patch("chirp_api.handlers.posts_handler.validate_session_token")
    @patch("chirp_api.handlers.posts_handler.SessionLocal")
    def test_create_post_success(
        self, mock_session_cls, mock_validate, mock_create, servicer, context, valid_auth
    ):
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_validate.return_value = valid_auth
        mock_create.return_value = {"post_id": "post-123"}

        request = posts_pb2.CreatePostRequest(
            content="Hello world!",
            session_token="valid-token",
        )

        response = servicer.CreatePost(request, context)

        assert response.success is True
        assert response.post_id == "post-123"

    @patch("chirp_api.handlers.posts_handler.validate_session_token")
    def test_create_post_no_auth(self, mock_validate, servicer, context):
        mock_validate.side_effect = Exception("Authentication required")

        request = posts_pb2.CreatePostRequest(
            content="Hello!",
            session_token="",
        )

        response = servicer.CreatePost(request, context)

        assert response.success is False
        assert "Authentication" in response.error


class TestGetPost:
    @patch("chirp_api.handlers.posts_handler.get_post")
    @patch("chirp_api.handlers.posts_handler.SessionLocal")
    def test_get_post(self, mock_session_cls, mock_get_post, servicer, context):
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_get_post.return_value = {
            "id": "post-123",
            "content": "Hello world!",
            "created_at": 1700000000,
            "updated_at": 1700000000,
            "author": {
                "id": "user-123",
                "username": "testuser",
                "display_name": "Test User",
                "avatar_url": None,
            },
            "like_count": 5,
            "comment_count": 2,
            "is_liked": False,
        }

        request = posts_pb2.GetPostRequest(post_id="post-123")
        response = servicer.GetPost(request, context)

        assert response.id == "post-123"
        assert response.content == "Hello world!"
        assert response.like_count == 5
        assert response.comment_count == 2


class TestGetPosts:
    @patch("chirp_api.handlers.posts_handler.get_posts")
    @patch("chirp_api.handlers.posts_handler.SessionLocal")
    def test_get_posts(self, mock_session_cls, mock_get_posts, servicer, context):
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_get_posts.return_value = [
            {
                "id": "post-1",
                "content": "Post 1",
                "created_at": 1700000000,
                "updated_at": 1700000000,
                "author": {
                    "id": "user-1",
                    "username": "user1",
                    "display_name": "User 1",
                    "avatar_url": None,
                },
                "like_count": 0,
                "comment_count": 0,
                "is_liked": False,
            },
        ]

        request = posts_pb2.GetPostsRequest(
            pagination=PaginationRequest(limit=20, offset=0),
        )
        response = servicer.GetPosts(request, context)

        assert len(response.posts) == 1
        assert response.posts[0].id == "post-1"


class TestUpdatePost:
    @patch("chirp_api.handlers.posts_handler.update_post")
    @patch("chirp_api.handlers.posts_handler.validate_session_token")
    @patch("chirp_api.handlers.posts_handler.SessionLocal")
    def test_update_post_success(
        self, mock_session_cls, mock_validate, mock_update, servicer, context, valid_auth
    ):
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_validate.return_value = valid_auth
        mock_update.return_value = {"success": True}

        request = posts_pb2.UpdatePostRequest(
            post_id="post-123",
            content="Updated!",
            session_token="valid-token",
        )

        response = servicer.UpdatePost(request, context)

        assert response.success is True


class TestDeletePost:
    @patch("chirp_api.handlers.posts_handler.delete_post")
    @patch("chirp_api.handlers.posts_handler.validate_session_token")
    @patch("chirp_api.handlers.posts_handler.SessionLocal")
    def test_delete_post_success(
        self, mock_session_cls, mock_validate, mock_delete, servicer, context, valid_auth
    ):
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_validate.return_value = valid_auth
        mock_delete.return_value = {"success": True}

        request = posts_pb2.DeletePostRequest(
            post_id="post-123",
            session_token="valid-token",
        )

        response = servicer.DeletePost(request, context)

        assert response.success is True
