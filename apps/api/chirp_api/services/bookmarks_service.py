"""Bookmarks service for Chirp API.

ISSUE 2 FIX: get_bookmarked_posts() previously issued 4 queries per
bookmarked post (post+author, like count, comment count, is_liked check).
For 10 bookmarks that was 41 queries. Replaced with bulk_get_post_stats()
for 4 queries total regardless of bookmark count.
"""

from sqlalchemy import and_, desc, select
from sqlalchemy.orm import Session

from chirp_api.db.models import Bookmark, Post, User
from chirp_api.services.query_helpers import attach_post_stats, bulk_get_post_stats
from chirp_api.services.utils import generate_id


def toggle_bookmark(session: Session, post_id: str, user_id: str) -> dict:
    """Toggle bookmark for a post.

    Returns dict with bookmarked boolean.
    Raises Exception if post not found.
    """
    assert isinstance(post_id, str) and len(post_id) > 0, "post_id must be non-empty"
    assert isinstance(user_id, str) and len(user_id) > 0, "user_id must be non-empty"

    # Verify post exists
    post = session.execute(select(Post).where(Post.id == post_id)).scalar_one_or_none()

    if not post:
        raise Exception("Post not found")

    # Check if already bookmarked
    existing_bookmark = session.execute(
        select(Bookmark).where(and_(Bookmark.post_id == post_id, Bookmark.user_id == user_id))
    ).scalar_one_or_none()

    if existing_bookmark:
        session.delete(existing_bookmark)
        session.commit()
        return {"bookmarked": False}
    else:
        bookmark = Bookmark(
            id=generate_id(),
            post_id=post_id,
            user_id=user_id,
        )
        session.add(bookmark)
        session.commit()
        return {"bookmarked": True}


def get_bookmark_status(session: Session, post_id: str, user_id: str) -> dict:
    """Check if a user has bookmarked a post.

    Returns dict with bookmarked boolean.
    """
    bookmark = session.execute(
        select(Bookmark).where(and_(Bookmark.post_id == post_id, Bookmark.user_id == user_id))
    ).scalar_one_or_none()

    return {"bookmarked": bookmark is not None}


def get_bookmarked_posts(
    session: Session,
    user_id: str,
    requester_id: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list:
    """Get all bookmarked posts for a user with pagination.

    Returns list of post dicts.

    Before: 4 queries per post (post+author, like count, comment count, is_liked).
    After:  4 queries total regardless of post count.
    """
    assert isinstance(user_id, str) and len(user_id) > 0, "user_id must be non-empty"
    assert limit > 0 and limit <= 100, "Limit must be between 1 and 100"
    assert offset >= 0, "Offset must be non-negative"

    # Query 1: bookmarked post IDs in order
    bookmarked_post_ids = session.execute(
        select(Bookmark.post_id)
        .where(Bookmark.user_id == user_id)
        .order_by(desc(Bookmark.created_at))
        .limit(limit)
        .offset(offset)
    ).scalars().all()

    if not bookmarked_post_ids:
        return []

    # Query 2: fetch all posts + authors in one join
    results = session.execute(
        select(Post, User)
        .outerjoin(User, Post.author_id == User.id)
        .where(Post.id.in_(bookmarked_post_ids))
    ).all()

    if not results:
        return []

    # Queries 3–4: bulk stats
    post_ids = [post.id for post, _ in results]
    stats = bulk_get_post_stats(session, post_ids, viewer_id=requester_id)

    # Re-order results to match bookmark order
    results_by_id = {post.id: (post, author) for post, author in results}
    ordered_results = [
        results_by_id[pid] for pid in bookmarked_post_ids if pid in results_by_id
    ]

    return attach_post_stats(ordered_results, stats)
