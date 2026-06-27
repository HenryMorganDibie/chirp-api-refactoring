"""Tests for comments_service — creating, listing, and deleting comments.

Uses real in-memory database via the session fixture. No mocking.
"""

import pytest

from chirp_api.services.comments_service import (
    create_comment,
    delete_comment,
    get_post_comments,
)
from tests.helpers import create_test_comment, create_test_post, create_test_user


class TestCreateComment:
    def test_create_comment(self, session):
        user = create_test_user(session)
        post = create_test_post(session, author_id=user.id)

        result = create_comment(session, post_id=post.id, content="Nice post!", author_id=user.id)

        assert result["comment_id"] is not None
        assert len(result["comment_id"]) > 0

    def test_create_nested_reply(self, session):
        user = create_test_user(session)
        post = create_test_post(session, author_id=user.id)
        parent = create_test_comment(session, post_id=post.id, author_id=user.id)

        result = create_comment(
            session,
            post_id=post.id,
            content="Reply!",
            author_id=user.id,
            parent_id=parent.id,
        )

        assert result["comment_id"] is not None

    def test_create_too_deep_reply(self, session):
        """Cannot reply to a reply — only one level of nesting allowed."""
        user = create_test_user(session)
        post = create_test_post(session, author_id=user.id)
        parent = create_test_comment(session, post_id=post.id, author_id=user.id)
        reply = create_test_comment(
            session, post_id=post.id, author_id=user.id, parent_id=parent.id
        )

        with pytest.raises(Exception, match="Cannot reply to a reply"):
            create_comment(
                session,
                post_id=post.id,
                content="Too deep!",
                author_id=user.id,
                parent_id=reply.id,
            )


class TestGetPostComments:
    def test_get_post_comments(self, session):
        user = create_test_user(session)
        post = create_test_post(session, author_id=user.id)
        create_test_comment(session, post_id=post.id, author_id=user.id, content="Comment 1")
        create_test_comment(session, post_id=post.id, author_id=user.id, content="Comment 2")

        results = get_post_comments(session, post.id)

        assert len(results) == 2
        for comment in results:
            assert "id" in comment
            assert "content" in comment
            assert "author" in comment
            assert "like_count" in comment
            assert "replies" in comment


class TestDeleteComment:
    def test_delete_comment(self, session):
        user = create_test_user(session)
        post = create_test_post(session, author_id=user.id)
        comment = create_test_comment(session, post_id=post.id, author_id=user.id)

        result = delete_comment(session, comment.id, user.id)

        assert result["success"] is True

    def test_delete_comment_not_owner(self, session):
        user1 = create_test_user(session)
        user2 = create_test_user(session)
        post = create_test_post(session, author_id=user1.id)
        comment = create_test_comment(session, post_id=post.id, author_id=user1.id)

        with pytest.raises(Exception, match="only delete your own"):
            delete_comment(session, comment.id, user2.id)
