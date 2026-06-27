"""Tests for Issue 2: Query Performance Problem.

Documents and verifies before/after query counts for the three
identified worst-offender operations.

Before fix:
  home feed (10 posts):       31 queries  (1 feed + 3 per post)
  user profile posts (N):     3N+1 queries
  bookmarks page (10 posts):  41 queries  (1 bookmarks + 4 per post)

After fix:
  home feed (10 posts):       3 queries   (1 feed + 2 bulk stats)
  user profile posts (N):     3 queries   (1 user + 1 posts + 2 bulk stats)
  bookmarks page (10 posts):  4 queries   (1 bookmarks + 1 posts + 2 bulk stats)

Uses SQLAlchemy event listeners to count actual DB round trips.
"""

import pytest
from sqlalchemy import event

from chirp_api.services.bookmarks_service import get_bookmarked_posts, toggle_bookmark
from chirp_api.services.feed_service import get_home_feed
from chirp_api.services.posts_service import get_posts, get_user_posts
from tests.helpers import (
    create_test_follow,
    create_test_like,
    create_test_post,
    create_test_user,
)


class QueryCounter:
    """Context manager that counts SQL statements executed against a session."""

    def __init__(self, session):
        self.session = session
        self.count = 0
        self._listener = None

    def __enter__(self):
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            self.count += 1

        self._listener = before_cursor_execute
        event.listen(self.session.bind, "before_cursor_execute", self._listener)
        return self

    def __exit__(self, *args):
        event.remove(self.session.bind, "before_cursor_execute", self._listener)


class TestHomeFeedQueryCount:
    def test_home_feed_uses_bounded_queries(self, session):
        """Home feed for 10 posts must not exceed 5 queries (was 31)."""
        viewer = create_test_user(session)
        author = create_test_user(session)
        create_test_follow(session, follower_id=viewer.id, following_id=author.id)

        for i in range(10):
            post = create_test_post(session, author_id=author.id, content=f"Post {i}")
            create_test_like(session, user_id=viewer.id, post_id=post.id)

        with QueryCounter(session) as counter:
            posts = get_home_feed(session, viewer.id, limit=10)

        assert len(posts) == 10
        # Follows query + posts+authors join + 2 bulk stats = ~4 queries
        assert counter.count <= 5, (
            f"Expected <=5 queries for 10-post feed, got {counter.count}. "
            "N+1 pattern may have been reintroduced."
        )

    def test_home_feed_query_count_does_not_scale_with_posts(self, session):
        """Query count must stay flat as we add more posts."""
        viewer = create_test_user(session)
        author = create_test_user(session)
        create_test_follow(session, follower_id=viewer.id, following_id=author.id)

        for i in range(20):
            create_test_post(session, author_id=author.id, content=f"Post {i}")

        with QueryCounter(session) as counter_20:
            get_home_feed(session, viewer.id, limit=20)

        for i in range(30):
            create_test_post(session, author_id=author.id, content=f"More {i}")

        with QueryCounter(session) as counter_50:
            get_home_feed(session, viewer.id, limit=50)

        # Query count should not grow proportionally with post count
        assert counter_50.count <= counter_20.count + 2, (
            "Query count should not scale with the number of posts — N+1 detected."
        )


class TestUserPostsQueryCount:
    def test_user_posts_uses_bounded_queries(self, session):
        """Getting user posts for 15 posts must stay under 6 queries (was 46)."""
        author = create_test_user(session)
        liker = create_test_user(session)

        for i in range(15):
            post = create_test_post(session, author_id=author.id, content=f"Post {i}")
            create_test_like(session, user_id=liker.id, post_id=post.id)

        with QueryCounter(session) as counter:
            posts = get_user_posts(session, author.username, user_id=liker.id)

        assert len(posts) == 15
        assert counter.count <= 6, (
            f"Expected <=6 queries for user posts (15 posts), got {counter.count}."
        )


class TestBookmarksQueryCount:
    def test_bookmarks_uses_bounded_queries(self, session):
        """Bookmarks page for 10 posts must stay under 6 queries (was 41)."""
        owner = create_test_user(session)
        author = create_test_user(session)

        for i in range(10):
            post = create_test_post(session, author_id=author.id, content=f"Post {i}")
            toggle_bookmark(session, post_id=post.id, user_id=owner.id)

        with QueryCounter(session) as counter:
            posts = get_bookmarked_posts(session, user_id=owner.id, requester_id=owner.id)

        assert len(posts) == 10
        assert counter.count <= 6, (
            f"Expected <=6 queries for 10 bookmarks, got {counter.count}."
        )


class TestResponseShapePreserved:
    def test_feed_response_shape_unchanged(self, session):
        """API response shape must be identical after the N+1 fix."""
        user = create_test_user(session)
        post = create_test_post(session, author_id=user.id, content="Hello")

        posts = get_home_feed(session, user.id)

        assert len(posts) == 1
        p = posts[0]
        assert "id" in p
        assert "content" in p
        assert "created_at" in p
        assert "updated_at" in p
        assert "like_count" in p
        assert "comment_count" in p
        assert "is_liked" in p
        assert "author" in p
        assert "id" in p["author"]
        assert "username" in p["author"]
        assert "display_name" in p["author"]
        assert "avatar_url" in p["author"]

    def test_bookmarks_response_shape_unchanged(self, session):
        """Bookmarks response shape must be identical after the N+1 fix."""
        owner = create_test_user(session)
        author = create_test_user(session)
        post = create_test_post(session, author_id=author.id, content="Bookmarked post")
        toggle_bookmark(session, post_id=post.id, user_id=owner.id)

        posts = get_bookmarked_posts(session, user_id=owner.id, requester_id=owner.id)

        assert len(posts) == 1
        p = posts[0]
        for field in ["id", "content", "created_at", "updated_at",
                      "like_count", "comment_count", "is_liked", "author"]:
            assert field in p, f"Missing field '{field}' in bookmark response"
