"""Posts service for Chirp API.

ISSUE 2 FIX: Replaced per-post N+1 _get_post_counts() calls with
bulk_get_post_stats() from query_helpers in get_posts() and get_user_posts().
Single-post operations (get_post) retain targeted queries since N=1.
"""

import time

from sqlalchemy import and_, desc, func, select
from sqlalchemy.orm import Session

from chirp_api.db.models import Comment, Like, Post, User
from chirp_api.services.mentions_service import process_mentions
from chirp_api.services.query_helpers import attach_post_stats, bulk_get_post_stats
from chirp_api.services.utils import generate_id


def _get_post_counts(session: Session, post_id: str, user_id: str | None = None) -> dict:
    """Get like count, comment count, and user like status for a single post.

    Used only for single-post lookups (get_post). For lists, use bulk_get_post_stats.
    """
    like_count = (
        session.execute(
            select(func.count()).select_from(Like).where(Like.post_id == post_id)
        ).scalar()
        or 0
    )

    comment_count = (
        session.execute(
            select(func.count()).select_from(Comment).where(Comment.post_id == post_id)
        ).scalar()
        or 0
    )

    is_liked = False
    if user_id:
        like_status = session.execute(
            select(Like).where(and_(Like.post_id == post_id, Like.user_id == user_id))
        ).scalar_one_or_none()
        is_liked = like_status is not None

    return {
        "like_count": like_count,
        "comment_count": comment_count,
        "is_liked": is_liked,
    }


def create_post(session: Session, content: str, author_id: str) -> dict:
    """Create a new post.

    Returns dict with post_id.
    Raises Exception if content is empty or too long.
    """
    if not content or len(content) == 0:
        raise Exception("Post content is required")

    if len(content) > 280:
        raise Exception("Post content must be 280 characters or less")

    post_id = generate_id()
    post = Post(
        id=post_id,
        content=content,
        author_id=author_id,
    )
    session.add(post)
    session.commit()

    # Process mentions and create notifications
    process_mentions(session, content, author_id, post_id)

    return {"post_id": post_id}


def get_post(session: Session, post_id: str, user_id: str | None = None) -> dict:
    """Get a single post by ID with author info and counts.

    Returns dict with post fields, author, and counts.
    Raises Exception if post not found.
    """
    assert isinstance(post_id, str) and len(post_id) > 0, "post_id must be a non-empty string"

    result = session.execute(
        select(Post, User).outerjoin(User, Post.author_id == User.id).where(Post.id == post_id)
    ).first()

    if not result:
        raise Exception("Post not found")

    post, author = result
    counts = _get_post_counts(session, post_id, user_id)

    return {
        "id": post.id,
        "content": post.content,
        "created_at": post.created_at,
        "updated_at": post.updated_at,
        "author": {
            "id": author.id if author else None,
            "username": author.username if author else None,
            "display_name": author.display_name if author else None,
            "avatar_url": author.avatar_url if author else None,
        },
        **counts,
    }


def update_post(session: Session, post_id: str, content: str, user_id: str) -> dict:
    """Update a post's content.

    Returns dict with success boolean.
    Raises Exception if post not found, not owned by user, or edit window expired.
    """
    if not content or len(content) == 0:
        raise Exception("Post content is required")

    if len(content) > 280:
        raise Exception("Post content must be 280 characters or less")

    post = session.execute(select(Post).where(Post.id == post_id)).scalar_one_or_none()

    if not post:
        raise Exception("Post not found")

    if post.author_id != user_id:
        raise Exception("You can only edit your own posts")

    # Check edit window (5 minutes)
    now = int(time.time())
    post_time = post.created_at
    if now - post_time > 300:
        raise Exception("Edit window has expired (5 minutes)")

    post.content = content
    post.updated_at = int(time.time())
    session.commit()

    return {"success": True}


def delete_post(session: Session, post_id: str, user_id: str) -> dict:
    """Delete a post.

    Returns dict with success boolean.
    Raises Exception if post not found or not owned by user.
    """
    post = session.execute(select(Post).where(Post.id == post_id)).scalar_one_or_none()

    if not post:
        raise Exception("Post not found")

    if post.author_id != user_id:
        raise Exception("You can only delete your own posts")

    session.delete(post)
    session.commit()

    return {"success": True}


def get_posts(
    session: Session, limit: int = 20, offset: int = 0, user_id: str | None = None
) -> list:
    """Get paginated posts with author info and counts.

    Returns list of post dicts.
    """
    assert limit > 0 and limit <= 100, "Limit must be between 1 and 100"
    assert offset >= 0, "Offset must be non-negative"

    results = session.execute(
        select(Post, User)
        .outerjoin(User, Post.author_id == User.id)
        .order_by(desc(Post.created_at))
        .limit(limit)
        .offset(offset)
    ).all()

    if not results:
        return []

    post_ids = [post.id for post, _ in results]
    stats = bulk_get_post_stats(session, post_ids, viewer_id=user_id)

    return attach_post_stats(results, stats)


def get_user_posts(session: Session, username: str, user_id: str | None = None) -> list:
    """Get all posts by a specific user.

    Returns list of post dicts.
    Raises Exception if user not found.
    """
    assert isinstance(username, str) and len(username) > 0, "Username must be a non-empty string"

    user = session.execute(select(User).where(User.username == username)).scalar_one_or_none()

    if not user:
        raise Exception("User not found")

    results = session.execute(
        select(Post, User)
        .outerjoin(User, Post.author_id == User.id)
        .where(Post.author_id == user.id)
        .order_by(desc(Post.created_at))
    ).all()

    if not results:
        return []

    post_ids = [post.id for post, _ in results]
    stats = bulk_get_post_stats(session, post_ids, viewer_id=user_id)

    return attach_post_stats(results, stats)
