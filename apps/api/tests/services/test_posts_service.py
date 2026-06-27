"""Tests for posts_service — CRUD operations and post listing.

Uses real in-memory database via the session fixture. No mocking.
"""

import pytest

from chirp_api.services.posts_service import (
    create_post,
    delete_post,
    get_post,
    get_posts,
    update_post,
)
from tests.helpers import create_test_post, create_test_user


class TestCreatePost:
    def test_create_post(self, session):
        user = create_test_user(session)
        result = create_post(session, content="Hello world!", author_id=user.id)

        assert result["post_id"] is not None
        assert len(result["post_id"]) > 0

    def test_create_post_too_long(self, session):
        user = create_test_user(session)
        long_content = "x" * 281

        with pytest.raises(Exception, match="280 characters or less"):
            create_post(session, content=long_content, author_id=user.id)

    def test_create_post_empty(self, session):
        user = create_test_user(session)

        with pytest.raises(Exception, match="content is required"):
            create_post(session, content="", author_id=user.id)


class TestGetPost:
    def test_get_post(self, session):
        user = create_test_user(session)
        post = create_test_post(session, author_id=user.id, content="My post")

        result = get_post(session, post.id)

        assert result["id"] == post.id
        assert result["content"] == "My post"
        assert result["author"]["id"] == user.id
        assert result["like_count"] == 0
        assert result["comment_count"] == 0

    def test_get_post_not_found(self, session):
        with pytest.raises(Exception, match="Post not found"):
            get_post(session, "nonexistent-id")


class TestUpdatePost:
    def test_update_post(self, session):
        user = create_test_user(session)
        post = create_test_post(session, author_id=user.id, content="Original")

        result = update_post(session, post.id, "Updated content", user.id)

        assert result["success"] is True

    def test_update_post_not_owner(self, session):
        user1 = create_test_user(session)
        user2 = create_test_user(session)
        post = create_test_post(session, author_id=user1.id)

        with pytest.raises(Exception, match="only edit your own"):
            update_post(session, post.id, "Hacked", user2.id)


class TestDeletePost:
    def test_delete_post(self, session):
        user = create_test_user(session)
        post = create_test_post(session, author_id=user.id)

        result = delete_post(session, post.id, user.id)

        assert result["success"] is True

        # Verify it's actually deleted
        with pytest.raises(Exception, match="Post not found"):
            get_post(session, post.id)


class TestGetPosts:
    def test_get_posts_with_counts(self, session):
        user = create_test_user(session)
        create_test_post(session, author_id=user.id, content="Post 1")
        create_test_post(session, author_id=user.id, content="Post 2")

        results = get_posts(session, limit=10, offset=0)

        assert len(results) == 2
        for post in results:
            assert "id" in post
            assert "content" in post
            assert "author" in post
            assert "like_count" in post
            assert "comment_count" in post
