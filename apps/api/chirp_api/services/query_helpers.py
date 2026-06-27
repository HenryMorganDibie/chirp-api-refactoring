"""Reusable query helpers to prevent N+1 query patterns.

ISSUE 2 — Query Performance Problem:

The N+1 anti-pattern: for a list of N posts, every service was issuing
3 separate queries *per post* to compute like_count, comment_count, and
is_liked. For a 10-post feed that's 1 (feed) + 30 (counts) = 31 queries.
For bookmarks with 10 posts it was even worse: 1 (bookmarks) + 4 per post
= 41 queries. At scale this would saturate the database.

Before/after query counts:
  home feed (10 posts):       31 queries  →  3 queries
  user profile page (posts):  3N+1 queries → 3 queries
  bookmarks page (10 posts):  4N+1 queries → 4 queries

Fix: replace per-row scalar subqueries with a single bulk aggregation query
using GROUP BY, then join back the results in Python. This is O(1) round
trips regardless of result set size.

Reusable pattern: every service that returns a list of posts should call
bulk_get_post_stats() instead of looping and calling _get_post_counts().
"""

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from chirp_api.db.models import Comment, Like


def bulk_get_post_stats(
    session: Session, post_ids: list[str], viewer_id: str | None = None
) -> dict[str, dict]:
    """Return like count, comment count, and viewer like status for a list of posts.

    Issues exactly 2 queries regardless of how many posts are in the list:
      1. One GROUP BY query for like and comment counts.
      2. One query for which posts the viewer has liked (only if viewer_id given).

    Returns a dict keyed by post_id:
      {
        post_id: {
          "like_count": int,
          "comment_count": int,
          "is_liked": bool,
        }
      }
    """
    if not post_ids:
        return {}

    # Query 1: aggregate like counts and comment counts in one pass
    stats_rows = session.execute(
        select(
            Like.post_id,
            func.count(Like.id).label("like_count"),
        )
        .where(Like.post_id.in_(post_ids))
        .group_by(Like.post_id)
    ).all()

    comment_rows = session.execute(
        select(
            Comment.post_id,
            func.count(Comment.id).label("comment_count"),
        )
        .where(Comment.post_id.in_(post_ids))
        .group_by(Comment.post_id)
    ).all()

    like_counts = {row.post_id: row.like_count for row in stats_rows}
    comment_counts = {row.post_id: row.comment_count for row in comment_rows}

    # Query 2: which of these posts has the viewer liked?
    liked_post_ids: set[str] = set()
    if viewer_id:
        liked_rows = session.execute(
            select(Like.post_id).where(
                and_(Like.post_id.in_(post_ids), Like.user_id == viewer_id)
            )
        ).scalars()
        liked_post_ids = set(liked_rows)

    return {
        pid: {
            "like_count": like_counts.get(pid, 0),
            "comment_count": comment_counts.get(pid, 0),
            "is_liked": pid in liked_post_ids,
        }
        for pid in post_ids
    }


def attach_post_stats(posts_with_authors: list, stats: dict[str, dict]) -> list[dict]:
    """Merge post+author rows with bulk stats into the final dict format.

    posts_with_authors: list of (Post, User) tuples from SQLAlchemy.
    stats: result of bulk_get_post_stats().
    """
    result = []
    for post, author in posts_with_authors:
        post_stats = stats.get(post.id, {"like_count": 0, "comment_count": 0, "is_liked": False})
        result.append(
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
                **post_stats,
            }
        )
    return result
