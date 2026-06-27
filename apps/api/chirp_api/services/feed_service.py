"""Feed service for Chirp API.

ISSUE 2 FIX: Replaced per-post N+1 _get_post_counts() calls with
bulk_get_post_stats() from query_helpers. Feed of 10 posts now issues
3 queries total instead of 31.
"""

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from chirp_api.db.models import Follow, Post, User
from chirp_api.services.query_helpers import attach_post_stats, bulk_get_post_stats


def get_home_feed(
    session: Session,
    user_id: str,
    limit: int = 20,
    offset: int = 0,
) -> list:
    """Get home feed: posts from followed users + own posts.

    Returns list of post dicts.
    """
    assert isinstance(user_id, str) and len(user_id) > 0, "user_id must be non-empty"
    assert limit > 0 and limit <= 100, "Limit must be between 1 and 100"
    assert offset >= 0, "Offset must be non-negative"

    # Get users that the current user follows
    following = (
        session.execute(select(Follow.following_id).where(Follow.follower_id == user_id))
        .scalars()
        .all()
    )

    following_ids = list(following)
    user_ids = [*following_ids, user_id]

    if len(user_ids) == 0:
        return []

    # Query 1: posts + authors
    results = session.execute(
        select(Post, User)
        .outerjoin(User, Post.author_id == User.id)
        .where(Post.author_id.in_(user_ids))
        .order_by(desc(Post.created_at))
        .limit(limit)
        .offset(offset)
    ).all()

    if not results:
        return []

    # Queries 2–3: bulk stats (2 aggregate queries regardless of post count)
    post_ids = [post.id for post, _ in results]
    stats = bulk_get_post_stats(session, post_ids, viewer_id=user_id)

    return attach_post_stats(results, stats)


def get_explore_feed(
    session: Session,
    limit: int = 20,
    offset: int = 0,
    user_id: str | None = None,
) -> list:
    """Get explore feed: all posts ordered by recency.

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
