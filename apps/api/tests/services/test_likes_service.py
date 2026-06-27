"""Tests for likes_service — toggling and checking like status.

Uses real in-memory database via the session fixture. No mocking.
"""

from chirp_api.services.likes_service import (
    get_comment_like_status,
    get_post_like_status,
    toggle_comment_like,
    toggle_post_like,
)
from tests.helpers import create_test_comment, create_test_post, create_test_user


class TestTogglePostLike:
    def test_toggle_post_like_on(self, session):
        user = create_test_user(session)
        post = create_test_post(session, author_id=user.id)

        result = toggle_post_like(session, post.id, user.id)

        assert result["liked"] is True

    def test_toggle_post_like_off(self, session):
        user = create_test_user(session)
        post = create_test_post(session, author_id=user.id)

        # Like it
        toggle_post_like(session, post.id, user.id)
        # Unlike it
        result = toggle_post_like(session, post.id, user.id)

        assert result["liked"] is False


class TestToggleCommentLike:
    def test_toggle_comment_like(self, session):
        user = create_test_user(session)
        post = create_test_post(session, author_id=user.id)
        comment = create_test_comment(session, post_id=post.id, author_id=user.id)

        result = toggle_comment_like(session, comment.id, user.id)

        assert result["liked"] is True


class TestGetLikeStatus:
    def test_get_post_like_status(self, session):
        user = create_test_user(session)
        post = create_test_post(session, author_id=user.id)

        # Not liked yet
        result = get_post_like_status(session, post.id, user.id)
        assert result["liked"] is False

        # Like it
        toggle_post_like(session, post.id, user.id)

        # Now liked
        result = get_post_like_status(session, post.id, user.id)
        assert result["liked"] is True

    def test_get_comment_like_status(self, session):
        user = create_test_user(session)
        post = create_test_post(session, author_id=user.id)
        comment = create_test_comment(session, post_id=post.id, author_id=user.id)

        result = get_comment_like_status(session, comment.id, user.id)
        assert result["liked"] is False
