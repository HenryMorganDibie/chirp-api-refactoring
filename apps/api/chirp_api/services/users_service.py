"""Users service for Chirp API."""

import time

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from chirp_api.db.models import Follow, Post, User


def get_user(session: Session, username: str, requester_id: str | None = None) -> dict:
    """Get user profile by username.

    Returns dict with user fields and counts.
    Raises Exception if user not found.
    """
    assert isinstance(username, str) and len(username) > 0, "Username must be non-empty"

    # Query 1: user
    user = session.execute(select(User).where(User.username == username)).scalar_one_or_none()

    if not user:
        raise Exception("User not found")

    # Query 2: follower count
    follower_count = (
        session.execute(
            select(func.count()).select_from(Follow).where(Follow.following_id == user.id)
        ).scalar()
        or 0
    )

    # Query 3: following count
    following_count = (
        session.execute(
            select(func.count()).select_from(Follow).where(Follow.follower_id == user.id)
        ).scalar()
        or 0
    )

    # Query 4: post count
    post_count = (
        session.execute(
            select(func.count()).select_from(Post).where(Post.author_id == user.id)
        ).scalar()
        or 0
    )

    # Query 5: is following check
    is_following = False
    if requester_id and requester_id != user.id:
        follow = session.execute(
            select(Follow).where(
                and_(Follow.follower_id == requester_id, Follow.following_id == user.id)
            )
        ).scalar_one_or_none()
        is_following = follow is not None

    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "display_name": user.display_name,
        "avatar_url": user.avatar_url,
        "bio": user.bio,
        "role": user.role,
        "created_at": user.created_at,
        "follower_count": follower_count,
        "following_count": following_count,
        "post_count": post_count,
        "is_following": is_following,
    }


def update_profile(
    session: Session,
    user_id: str,
    display_name: str | None = None,
    bio: str | None = None,
    avatar_url: str | None = None,
) -> dict:
    """Update user profile fields.

    Returns dict with success boolean.
    Only updates fields that are provided (not None).
    """
    assert isinstance(user_id, str) and len(user_id) > 0, "user_id must be non-empty"

    user = session.execute(select(User).where(User.id == user_id)).scalar_one_or_none()

    if not user:
        raise Exception("User not found")

    has_updates = False

    if display_name is not None:
        user.display_name = display_name
        has_updates = True

    if bio is not None:
        user.bio = bio
        has_updates = True

    if avatar_url is not None:
        user.avatar_url = avatar_url
        has_updates = True

    if has_updates:
        user.updated_at = int(time.time())
        session.commit()

    return {"success": True}
