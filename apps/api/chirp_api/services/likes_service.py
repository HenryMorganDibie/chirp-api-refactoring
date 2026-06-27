"""Likes service for Chirp API.

Handles toggling and checking like status for posts and comments.
No N+1 issues in this service — it operates on single entities.
"""

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from chirp_api.db.models import Comment, Like, Post
from chirp_api.services.notifications_service import create_notification
from chirp_api.services.utils import generate_id


def toggle_post_like(session: Session, post_id: str, user_id: str) -> dict:
    """Toggle a like on a post.

    Returns dict with liked boolean.
    Raises Exception if post not found.
    """
    assert isinstance(post_id, str) and len(post_id) > 0, "post_id must be non-empty"
    assert isinstance(user_id, str) and len(user_id) > 0, "user_id must be non-empty"

    # Verify post exists
    post = session.execute(select(Post).where(Post.id == post_id)).scalar_one_or_none()

    if not post:
        raise Exception("Post not found")

    # Check if already liked
    existing_like = session.execute(
        select(Like).where(and_(Like.post_id == post_id, Like.user_id == user_id))
    ).scalar_one_or_none()

    if existing_like:
        # Unlike
        session.delete(existing_like)
        session.commit()
        return {"liked": False}
    else:
        # Like
        like = Like(
            id=generate_id(),
            post_id=post_id,
            user_id=user_id,
        )
        session.add(like)
        session.commit()

        # Create notification for post author
        create_notification(
            session,
            user_id=post.author_id,
            notification_type="like",
            actor_id=user_id,
            post_id=post_id,
        )

        return {"liked": True}


def toggle_comment_like(session: Session, comment_id: str, user_id: str) -> dict:
    """Toggle a like on a comment.

    Returns dict with liked boolean.
    Raises Exception if comment not found.
    """
    assert isinstance(comment_id, str) and len(comment_id) > 0, "comment_id must be non-empty"
    assert isinstance(user_id, str) and len(user_id) > 0, "user_id must be non-empty"

    # Verify comment exists
    comment = session.execute(select(Comment).where(Comment.id == comment_id)).scalar_one_or_none()

    if not comment:
        raise Exception("Comment not found")

    # Check if already liked
    existing_like = session.execute(
        select(Like).where(and_(Like.comment_id == comment_id, Like.user_id == user_id))
    ).scalar_one_or_none()

    if existing_like:
        # Unlike
        session.delete(existing_like)
        session.commit()
        return {"liked": False}
    else:
        # Like
        like = Like(
            id=generate_id(),
            comment_id=comment_id,
            user_id=user_id,
        )
        session.add(like)
        session.commit()

        # Create notification for comment author
        create_notification(
            session,
            user_id=comment.author_id,
            notification_type="like",
            actor_id=user_id,
            comment_id=comment_id,
        )

        return {"liked": True}


def get_post_like_status(session: Session, post_id: str, user_id: str) -> dict:
    """Check if a user has liked a post.

    Returns dict with liked boolean.
    """
    like = session.execute(
        select(Like).where(and_(Like.post_id == post_id, Like.user_id == user_id))
    ).scalar_one_or_none()

    return {"liked": like is not None}


def get_comment_like_status(session: Session, comment_id: str, user_id: str) -> dict:
    """Check if a user has liked a comment.

    Returns dict with liked boolean.
    """
    like = session.execute(
        select(Like).where(and_(Like.comment_id == comment_id, Like.user_id == user_id))
    ).scalar_one_or_none()

    return {"liked": like is not None}
