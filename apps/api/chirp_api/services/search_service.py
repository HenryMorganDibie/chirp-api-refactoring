"""Search service for Chirp API."""

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.orm import Session

from chirp_api.db.models import Comment, Like, Post, User


def _get_post_counts(session: Session, post_id: str, user_id: str | None = None) -> dict:
    """Get like count, comment count, and user like status for a single post."""
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


def search_posts(session: Session, query: str, user_id: str | None = None) -> list:
    """Search posts by content with LIKE pattern.

    Returns list of post dicts. Returns empty list if query is empty.
    """
    if not query or len(query.strip()) == 0:
        return []

    search_pattern = f"%{query}%"

    results = session.execute(
        select(Post, User)
        .outerjoin(User, Post.author_id == User.id)
        .where(Post.content.like(search_pattern))
        .order_by(desc(Post.created_at))
        .limit(50)
    ).all()

    posts_with_counts = []
    for post, author in results:
        counts = _get_post_counts(session, post.id, user_id)
        posts_with_counts.append(
            {
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
        )

    return posts_with_counts


def search_users(session: Session, query: str) -> list:
    """Search users by username or display name with LIKE pattern.

    Returns list of user dicts. Returns empty list if query is empty.
    """
    if not query or len(query.strip()) == 0:
        return []

    search_pattern = f"%{query}%"

    results = (
        session.execute(
            select(User)
            .where(
                or_(
                    User.username.like(search_pattern),
                    User.display_name.like(search_pattern),
                )
            )
            .limit(20)
        )
        .scalars()
        .all()
    )

    return [
        {
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "avatar_url": user.avatar_url,
            "bio": user.bio,
        }
        for user in results
    ]
