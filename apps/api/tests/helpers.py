"""Test data creation helpers for Chirp API tests.

Provides factory functions for creating test entities in the database.
Each helper uses generate_id() and hash_password() from the real service utilities.
"""

from sqlalchemy.orm import Session

from chirp_api.db.models import Comment, Follow, Like, Post, User
from chirp_api.services.utils import generate_id, hash_password

_counter = 0


def _next_id():
    """Return an incrementing counter for unique test data."""
    global _counter
    _counter += 1
    return _counter


def create_test_user(session: Session, overrides: dict | None = None) -> User:
    """Create a test user with sensible defaults.

    Returns the created User ORM object.
    """
    n = _next_id()
    defaults = {
        "id": generate_id(),
        "email": f"test-{n}@example.com",
        "username": f"user-{n}",
        "display_name": f"Test User {n}",
        "password_hash": hash_password("password123"),
        "role": "user",
    }
    if overrides:
        defaults.update(overrides)

    user = User(**defaults)
    session.add(user)
    session.commit()
    return user


def create_test_post(session: Session, author_id: str, content: str = "Test post") -> Post:
    """Create a test post.

    Returns the created Post ORM object.
    """
    post = Post(
        id=generate_id(),
        content=content,
        author_id=author_id,
    )
    session.add(post)
    session.commit()
    return post


def create_test_comment(
    session: Session,
    post_id: str,
    author_id: str,
    content: str = "Test comment",
    parent_id: str | None = None,
) -> Comment:
    """Create a test comment.

    Returns the created Comment ORM object.
    """
    comment = Comment(
        id=generate_id(),
        content=content,
        post_id=post_id,
        author_id=author_id,
        parent_id=parent_id,
    )
    session.add(comment)
    session.commit()
    return comment


def create_test_like(
    session: Session,
    user_id: str,
    post_id: str | None = None,
    comment_id: str | None = None,
) -> Like:
    """Create a test like (on a post or comment).

    Returns the created Like ORM object.
    """
    like = Like(
        id=generate_id(),
        user_id=user_id,
        post_id=post_id,
        comment_id=comment_id,
    )
    session.add(like)
    session.commit()
    return like


def create_test_follow(session: Session, follower_id: str, following_id: str) -> Follow:
    """Create a test follow relationship.

    Returns the created Follow ORM object.
    """
    follow = Follow(
        id=generate_id(),
        follower_id=follower_id,
        following_id=following_id,
    )
    session.add(follow)
    session.commit()
    return follow
