"""Follows service for Chirp API.

Handles follow/unfollow, status checks, and follower/following counts.
Prevents self-follow.
"""

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from chirp_api.db.models import Follow, User
from chirp_api.services.notifications_service import create_notification
from chirp_api.services.utils import generate_id


def toggle_follow(session: Session, username: str, follower_id: str) -> dict:
    """Toggle follow on a user by username.

    Returns dict with following boolean.
    Raises Exception if user not found or self-follow attempted.
    """
    assert isinstance(username, str) and len(username) > 0, "Username must be non-empty"
    assert isinstance(follower_id, str) and len(follower_id) > 0, "follower_id must be non-empty"

    # Find user to follow
    user_to_follow = session.execute(
        select(User).where(User.username == username)
    ).scalar_one_or_none()

    if not user_to_follow:
        raise Exception("User not found")

    # Cannot follow yourself
    if user_to_follow.id == follower_id:
        raise Exception("You cannot follow yourself")

    # Check if already following
    existing_follow = session.execute(
        select(Follow).where(
            and_(Follow.follower_id == follower_id, Follow.following_id == user_to_follow.id)
        )
    ).scalar_one_or_none()

    if existing_follow:
        # Unfollow
        session.delete(existing_follow)
        session.commit()
        return {"following": False}
    else:
        # Follow
        follow = Follow(
            id=generate_id(),
            follower_id=follower_id,
            following_id=user_to_follow.id,
        )
        session.add(follow)
        session.commit()

        # Create notification for followed user
        create_notification(
            session,
            user_id=user_to_follow.id,
            notification_type="follow",
            actor_id=follower_id,
        )

        return {"following": True}


def get_follow_status(session: Session, username: str, follower_id: str) -> dict:
    """Check if follower_id follows the user with given username.

    Returns dict with following boolean.
    Raises Exception if user not found.
    """
    user_to_check = session.execute(
        select(User).where(User.username == username)
    ).scalar_one_or_none()

    if not user_to_check:
        raise Exception("User not found")

    follow = session.execute(
        select(Follow).where(
            and_(Follow.follower_id == follower_id, Follow.following_id == user_to_check.id)
        )
    ).scalar_one_or_none()

    return {"following": follow is not None}


def get_follower_count(session: Session, username: str) -> dict:
    """Get the number of followers for a user.

    Returns dict with count integer.
    Raises Exception if user not found.
    """
    user = session.execute(select(User).where(User.username == username)).scalar_one_or_none()

    if not user:
        raise Exception("User not found")

    count = (
        session.execute(
            select(func.count()).select_from(Follow).where(Follow.following_id == user.id)
        ).scalar()
        or 0
    )

    return {"count": count}


def get_following_count(session: Session, username: str) -> dict:
    """Get the number of users a user is following.

    Returns dict with count integer.
    Raises Exception if user not found.
    """
    user = session.execute(select(User).where(User.username == username)).scalar_one_or_none()

    if not user:
        raise Exception("User not found")

    count = (
        session.execute(
            select(func.count()).select_from(Follow).where(Follow.follower_id == user.id)
        ).scalar()
        or 0
    )

    return {"count": count}
