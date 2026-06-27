"""Comments service for Chirp API."""

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from chirp_api.db.models import Comment, Like, Post, User
from chirp_api.services.mentions_service import process_mentions
from chirp_api.services.notifications_service import create_notification
from chirp_api.services.utils import generate_id


def _get_comment_like_info(session: Session, comment_id: str, user_id: str | None = None) -> dict:
    """Get like count and user like status for a single comment."""
    # Query 1: like count
    like_count = (
        session.execute(
            select(func.count()).select_from(Like).where(Like.comment_id == comment_id)
        ).scalar()
        or 0
    )

    # Query 2: user like status
    is_liked = False
    if user_id:
        like_status = session.execute(
            select(Like).where(and_(Like.comment_id == comment_id, Like.user_id == user_id))
        ).scalar_one_or_none()
        is_liked = like_status is not None

    return {
        "like_count": like_count,
        "is_liked": is_liked,
    }


def create_comment(
    session: Session,
    post_id: str,
    content: str,
    author_id: str,
    parent_id: str | None = None,
) -> dict:
    """Create a new comment on a post.

    Returns dict with comment_id.
    Raises Exception if content empty, post not found, parent invalid, or nesting too deep.
    """
    if not content or len(content) == 0:
        raise Exception("Comment content is required")

    # Verify post exists
    post = session.execute(select(Post).where(Post.id == post_id)).scalar_one_or_none()

    if not post:
        raise Exception("Post not found")

    # If parentId provided, verify parent comment exists
    if parent_id:
        parent_comment = session.execute(
            select(Comment).where(Comment.id == parent_id)
        ).scalar_one_or_none()

        if not parent_comment:
            raise Exception("Parent comment not found")

        # Only allow one level of nesting
        if parent_comment.parent_id:
            raise Exception("Cannot reply to a reply")

    comment_id = generate_id()
    comment = Comment(
        id=comment_id,
        content=content,
        post_id=post_id,
        author_id=author_id,
        parent_id=parent_id or None,
    )
    session.add(comment)
    session.commit()

    # Create notification for post author
    create_notification(
        session,
        user_id=post.author_id,
        notification_type="comment",
        actor_id=author_id,
        post_id=post_id,
        comment_id=comment_id,
    )

    # Process mentions and create notifications
    process_mentions(session, content, author_id, post_id, comment_id)

    return {"comment_id": comment_id}


def get_post_comments(session: Session, post_id: str, user_id: str | None = None) -> list:
    """Get all comments for a post, with nested replies and like info.

    Returns list of comment dicts with nested replies.
    """
    # Get top-level comments (no parent)
    top_level_results = session.execute(
        select(Comment, User)
        .outerjoin(User, Comment.author_id == User.id)
        .where(and_(Comment.post_id == post_id, Comment.parent_id.is_(None)))
    ).all()

    comments_with_replies = []
    for comment, author in top_level_results:
        # like info per comment
        like_info = _get_comment_like_info(session, comment.id, user_id)

        # query replies for each comment
        reply_results = session.execute(
            select(Comment, User)
            .outerjoin(User, Comment.author_id == User.id)
            .where(Comment.parent_id == comment.id)
        ).all()

        replies_with_likes = []
        for reply, reply_author in reply_results:
            # like info per reply
            reply_like_info = _get_comment_like_info(session, reply.id, user_id)
            replies_with_likes.append(
                {
                    "id": reply.id,
                    "content": reply.content,
                    "created_at": reply.created_at,
                    "parent_id": reply.parent_id,
                    "author": {
                        "id": reply_author.id if reply_author else None,
                        "username": reply_author.username if reply_author else None,
                        "display_name": reply_author.display_name if reply_author else None,
                        "avatar_url": reply_author.avatar_url if reply_author else None,
                    },
                    **reply_like_info,
                    "replies": [],
                }
            )

        comments_with_replies.append(
            {
                "id": comment.id,
                "content": comment.content,
                "created_at": comment.created_at,
                "parent_id": comment.parent_id,
                "author": {
                    "id": author.id if author else None,
                    "username": author.username if author else None,
                    "display_name": author.display_name if author else None,
                    "avatar_url": author.avatar_url if author else None,
                },
                **like_info,
                "replies": replies_with_likes,
            }
        )

    return comments_with_replies


def delete_comment(session: Session, comment_id: str, user_id: str) -> dict:
    """Delete a comment.

    Returns dict with success boolean.
    Raises Exception if comment not found or not owned by user.
    """
    comment = session.execute(select(Comment).where(Comment.id == comment_id)).scalar_one_or_none()

    if not comment:
        raise Exception("Comment not found")

    if comment.author_id != user_id:
        raise Exception("You can only delete your own comments")

    session.delete(comment)
    session.commit()

    return {"success": True}
